using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace TheraQuest
{
    /// <summary>
    /// Talks to server.py. Authenticates with the patient's synthetic code only (DEC-009): the server
    /// accepts /api/vr/* from this machine and scopes every call to that one patient.
    ///
    /// If the server can't be reached, the app uses the last program the server sent for this patient
    /// (cached on disk, phase safety gate included). With no cached program there is no session:
    /// a hardcoded fallback could prescribe movements the patient isn't cleared for (M4.3).
    /// Finished sessions that can't be uploaded go to a queue file and are sent later; each carries a
    /// session_uuid, so a retry after a lost reply is not counted twice.
    /// </summary>
    public class ApiClient : MonoBehaviour
    {
        const int CacheSchema = 2;   // 2: exercises carry pose, posture, direction and checks (DEC-012)

        public string baseUrl = "http://127.0.0.1:8000";
        [Tooltip("Synthetic patient code from the therapist dashboard, e.g. P-001. " +
                 "A built player reads -patient from the command line or config.json instead.")]
        public string patientCode = "P-001";
        public float timeoutSeconds = 4f;

        /// <summary>Why the last program load fell back (shown on the menu), or null.</summary>
        public string LastProblem { get; private set; }
        public string Code => ClientConfig.NormalizeCode(patientCode);
        public int QueuedCount => SafeReadLines(QueuePath).Count;

        string QueuePath => Path.Combine(Application.persistentDataPath, "pending_sessions.jsonl");
        // Sessions the server refused (wrong patient, invalid data); kept, never deleted
        string RejectedPath => Path.Combine(Application.persistentDataPath, "rejected_sessions.jsonl");
        string CachePath => Path.Combine(Application.persistentDataPath, $"program_{SafeName(Code)}.json");

        [Serializable]
        class ProgramCache { public int schema; public string code; public string savedAt; public ProgramResponse program; }

        void Awake()
        {
            var cfg = ClientConfig.Current;
            string code = ClientConfig.Arg("patient");
            if (string.IsNullOrWhiteSpace(code)) code = cfg.patientCode;
            if (!string.IsNullOrWhiteSpace(code)) patientCode = code;
            string url = ClientConfig.Arg("server");
            if (string.IsNullOrWhiteSpace(url)) url = cfg.serverUrl;
            if (!string.IsNullOrWhiteSpace(url)) baseUrl = url.TrimEnd('/');
        }

        /// <summary>Therapist page: switch this computer to another patient (saved in config.json).</summary>
        public void SetPatientCode(string code)
        {
            patientCode = ClientConfig.NormalizeCode(code);
            var cfg = ClientConfig.Current;
            cfg.patientCode = patientCode;
            cfg.Save();
        }

        // ------------------------------------------------------------------ program
        public IEnumerator LoadProgram(Action<ProgramResponse, bool> done)
        {
            LastProblem = null;
            using (var req = UnityWebRequest.Get($"{baseUrl}/api/vr/program"))
            {
                req.SetRequestHeader("X-Patient-Code", Code);
                req.timeout = Mathf.CeilToInt(timeoutSeconds);
                yield return req.SendWebRequest();
                if (req.result == UnityWebRequest.Result.Success && TryParse(req.downloadHandler.text, out ProgramResponse data))
                {
                    ProgramRules.Clean(data);
                    SaveCache(data);
                    done(data, true);
                    yield return FlushQueue();
                    yield break;
                }
                if (req.responseCode == 401 || req.responseCode == 403)
                {
                    // The server answered but doesn't accept this code: a cached program would be for the wrong patient
                    LastProblem = $"The clinic server doesn't know patient code '{Code}'. Ask your therapist.";
                    Debug.LogWarning($"[TheraQuest] Server refused patient code '{Code}' ({req.responseCode}: {req.downloadHandler?.text}).");
                    done(NoProgram(), false);
                    yield break;
                }
                Debug.LogWarning($"[TheraQuest] Server not reachable or bad reply ({req.error}).");
                var cached = LoadCache();
                if (cached != null)
                {
                    LastProblem = "Offline: using the last program from your therapist.";
                    done(cached, false);
                }
                else
                {
                    LastProblem = "Can't reach the clinic server, and there is no saved program. Ask your therapist to start it.";
                    done(NoProgram(), false);
                }
            }
        }

        static bool TryParse<T>(string json, out T value) where T : class
        {
            try { value = JsonUtility.FromJson<T>(json); }
            catch (ArgumentException) { value = null; }
            return value != null;
        }

        void SaveCache(ProgramResponse p)
        {
            try
            {
                var c = new ProgramCache { schema = CacheSchema, code = Code, savedAt = DateTime.Now.ToString("s"), program = p };
                AtomicWrite(CachePath, JsonUtility.ToJson(c));
            }
            catch (IOException e) { Debug.LogWarning($"[TheraQuest] Could not cache program: {e.Message}"); }
        }

        ProgramResponse LoadCache()
        {
            try
            {
                if (!File.Exists(CachePath)) return null;
                if (!TryParse(File.ReadAllText(CachePath), out ProgramCache c)) return null;
                if (c.schema != CacheSchema || c.code != Code || c.program == null) return null;
                ProgramRules.Clean(c.program);
                return c.program;
            }
            catch (IOException) { return null; }
        }

        /// <summary>No program: no exercises, so no session can start.</summary>
        ProgramResponse NoProgram() => new ProgramResponse
        {
            patient = new PatientInfo { id = 0, code = Code, name = "", level = 1, xpForNext = 100 },
            program = new ProgramInfo { id = 0, name = "No program loaded", days = new int[0], maxReps = 0 },
            exercises = new ExerciseDef[0]
        };

        // ------------------------------------------------------------------ sessions
        public IEnumerator UploadSession(SessionUpload upload, Action<SessionResponse> done)
        {
            if (string.IsNullOrEmpty(upload.patient_code)) upload.patient_code = Code;
            if (string.IsNullOrEmpty(upload.session_uuid)) upload.session_uuid = Guid.NewGuid().ToString();
            string json = JsonUtility.ToJson(upload);
            SessionResponse resp = null;
            long status = 0;
            yield return Post(json, upload.patient_code, (r, s) => { resp = r; status = s; });
            if (resp == null)
            {
                if (IsPermanentRefusal(status)) Append(RejectedPath, json);
                else
                {
                    Append(QueuePath, json);
                    Debug.LogWarning("[TheraQuest] Session saved offline; it will upload when the server is back.");
                }
            }
            done(resp);
        }

        /// <summary>Save a session to the queue without trying the network (used when the app is closing).</summary>
        public void QueueOffline(SessionUpload upload)
        {
            if (string.IsNullOrEmpty(upload.patient_code)) upload.patient_code = Code;
            if (string.IsNullOrEmpty(upload.session_uuid)) upload.session_uuid = Guid.NewGuid().ToString();
            Append(QueuePath, JsonUtility.ToJson(upload));
        }

        /// <summary>
        /// 400, 403, 404 and 409 mean the server will never accept this upload; retrying forever would block
        /// the queue. 401 (unknown patient code) is a setup problem a therapist can fix, so it stays queued.
        /// </summary>
        public static bool IsPermanentRefusal(long status) => status >= 400 && status < 500 && status != 401 && status != 408 && status != 429;

        /// <summary>done(response, or null on failure; HTTP status code, 0 = no reply)</summary>
        IEnumerator Post(string json, string code, Action<SessionResponse, long> done)
        {
            using (var req = new UnityWebRequest($"{baseUrl}/api/vr/sessions", "POST"))
            {
                req.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes(json));
                req.downloadHandler = new DownloadHandlerBuffer();
                req.SetRequestHeader("Content-Type", "application/json");
                req.SetRequestHeader("X-Patient-Code", code);
                req.timeout = Mathf.CeilToInt(timeoutSeconds);
                yield return req.SendWebRequest();
                if (req.result == UnityWebRequest.Result.Success && TryParse(req.downloadHandler.text, out SessionResponse r))
                    done(r, req.responseCode);
                else
                {
                    Debug.LogWarning($"[TheraQuest] Upload failed: {req.responseCode} {req.error} {req.downloadHandler?.text}");
                    done(null, req.result == UnityWebRequest.Result.Success ? 0 : req.responseCode);
                }
            }
        }

        /// <summary>
        /// Sends queued sessions one by one. Each line leaves the queue file only after the server accepted
        /// it (or refused it for good, then it moves to the rejected file), so closing the app mid-flush loses nothing.
        /// </summary>
        IEnumerator FlushQueue()
        {
            var lines = SafeReadLines(QueuePath);
            while (lines.Count > 0)
            {
                string line = lines[0];
                if (!string.IsNullOrWhiteSpace(line))
                {
                    if (!TryParse(line, out SessionUpload u))
                    {
                        Append(RejectedPath, line);   // unreadable line: park it, don't retry forever
                    }
                    else
                    {
                        // Lines queued before DEC-009 carry no patient_code; they belong to the configured patient
                        string code = string.IsNullOrEmpty(u.patient_code) ? Code : u.patient_code;
                        SessionResponse r = null;
                        long status = 0;
                        yield return Post(line, code, (x, s) => { r = x; status = s; });
                        if (r == null && !IsPermanentRefusal(status)) yield break;   // server gone again: keep the rest
                        if (r == null)
                        {
                            Append(RejectedPath, line);
                            Debug.LogWarning($"[TheraQuest] Queued session refused ({status}); kept in {RejectedPath}.");
                        }
                    }
                }
                lines.RemoveAt(0);
                try { AtomicWrite(QueuePath, lines.Count > 0 ? string.Join("\n", lines) + "\n" : ""); }
                catch (IOException e) { Debug.LogWarning($"[TheraQuest] Could not update the queue: {e.Message}"); yield break; }
            }
        }

        // ------------------------------------------------------------------ files
        static List<string> SafeReadLines(string path)
        {
            try { return File.Exists(path) ? new List<string>(File.ReadAllLines(path)) : new List<string>(); }
            catch (IOException) { return new List<string>(); }
        }

        static void Append(string path, string line)
        {
            try { File.AppendAllText(path, line.Replace("\n", " ") + "\n"); }
            catch (IOException e) { Debug.LogError($"[TheraQuest] Could not write {path}: {e.Message}"); }
        }

        /// <summary>Write to a temp file, then swap it in, so a crash never leaves half a file.</summary>
        static void AtomicWrite(string path, string text)
        {
            string tmp = path + ".tmp";
            File.WriteAllText(tmp, text);
            if (File.Exists(path)) File.Replace(tmp, path, null);
            else File.Move(tmp, path);
        }

        static string SafeName(string s)
        {
            var sb = new StringBuilder();
            foreach (char ch in s) sb.Append(char.IsLetterOrDigit(ch) || ch == '-' ? ch : '_');
            return sb.Length > 0 ? sb.ToString() : "none";
        }
    }
}
