using System;
using System.Collections;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace TheraQuest
{
    /// <summary>
    /// Talks to server.py. If the server can't be reached, the app keeps working:
    /// it uses a built-in default program and saves finished sessions to a local
    /// queue file that is uploaded the next time the server is available.
    /// Authenticates with the patient's synthetic code only (DEC-009): the server
    /// accepts /api/vr/* from this machine and scopes every call to that one patient.
    /// </summary>
    public class ApiClient : MonoBehaviour
    {
        public string baseUrl = "http://127.0.0.1:8000";
        [Tooltip("Synthetic patient code from the therapist dashboard, e.g. P-001")]
        public string patientCode = "P-001";
        public float timeoutSeconds = 4f;

        string QueuePath => Path.Combine(Application.persistentDataPath, "pending_sessions.jsonl");
        // Sessions the server refused as belonging to another patient; kept, never deleted
        string RejectedPath => Path.Combine(Application.persistentDataPath, "rejected_sessions.jsonl");

        string Code => (patientCode ?? "").Trim().ToUpperInvariant();

        public IEnumerator LoadProgram(Action<ProgramResponse, bool> done)
        {
            using (var req = UnityWebRequest.Get($"{baseUrl}/api/vr/program"))
            {
                req.SetRequestHeader("X-Patient-Code", Code);
                req.timeout = Mathf.CeilToInt(timeoutSeconds);
                yield return req.SendWebRequest();
                if (req.result == UnityWebRequest.Result.Success)
                {
                    var data = JsonUtility.FromJson<ProgramResponse>(req.downloadHandler.text);
                    done(data, true);
                    yield return FlushQueue();
                }
                else if (req.responseCode == 401 || req.responseCode == 403)
                {
                    Debug.LogWarning($"[TheraQuest] Server refused patient code '{Code}' ({req.responseCode}: {req.downloadHandler?.text}). Using default program.");
                    done(DefaultProgram(), false);
                }
                else
                {
                    Debug.LogWarning($"[TheraQuest] Server not reachable ({req.error}). Using default program.");
                    done(DefaultProgram(), false);
                }
            }
        }

        public IEnumerator UploadSession(SessionUpload upload, Action<SessionResponse> done)
        {
            if (string.IsNullOrEmpty(upload.patient_code)) upload.patient_code = Code;
            string json = JsonUtility.ToJson(upload);
            SessionResponse resp = null;
            yield return Post(json, upload.patient_code, (r, _) => resp = r);
            if (resp == null)
            {
                File.AppendAllText(QueuePath, json + "\n");
                Debug.LogWarning("[TheraQuest] Session saved offline; it will upload when the server is back.");
            }
            done(resp);
        }

        /// <summary>done(response, or null on failure; HTTP status code)</summary>
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
                if (req.result == UnityWebRequest.Result.Success)
                    done(JsonUtility.FromJson<SessionResponse>(req.downloadHandler.text), req.responseCode);
                else
                {
                    Debug.LogWarning($"[TheraQuest] Upload failed: {req.error} {req.downloadHandler?.text}");
                    done(null, req.responseCode);
                }
            }
        }

        IEnumerator FlushQueue()
        {
            if (!File.Exists(QueuePath)) yield break;
            var lines = File.ReadAllLines(QueuePath);
            File.Delete(QueuePath);
            foreach (var line in lines)
            {
                if (string.IsNullOrWhiteSpace(line)) continue;
                // Lines queued before DEC-009 carry no patient_code; they belong to the configured patient
                string code = Code;
                try
                {
                    var u = JsonUtility.FromJson<SessionUpload>(line);
                    if (u != null && !string.IsNullOrEmpty(u.patient_code)) code = u.patient_code;
                }
                catch (ArgumentException) { }

                SessionResponse r = null;
                long status = 0;
                yield return Post(line, code, (x, s) => { r = x; status = s; });
                if (r != null) continue;
                if (status == 403)
                {
                    File.AppendAllText(RejectedPath, line + "\n");
                    Debug.LogWarning($"[TheraQuest] Queued session refused for patient '{code}'; kept in {RejectedPath}.");
                }
                else File.AppendAllText(QueuePath, line + "\n");
            }
        }

        public static ProgramResponse DefaultProgram()
        {
            return new ProgramResponse
            {
                // id 0 = unknown: an offline session is attributed by patient_code when it uploads
                patient = new PatientInfo { id = 0, code = "OFFLINE", name = "Offline test", level = 1, xpForNext = 100 },
                program = new ProgramInfo { id = 0, name = "Default program (offline)", days = new[] { 1, 3, 5 }, maxReps = 14 },
                exercises = new[]
                {
                    new ExerciseDef { id = 1, code = "shoulderAbd", name = "Shoulder abduction", joint = "Shoulder", measure = "shoulderElev", view = "front", position = "Standing, arm at your side, thumb up", side = "", targetAngle = 90, tolerance = 10, safetyMax = 120, sets = 1, restSeconds = 30, baseReps = 8, reps = 8, stage = 1, cue = "Raise your arm out to the side" },
                    new ExerciseDef { id = 2, code = "elbowFlex", name = "Elbow flexion", joint = "Elbow", measure = "elbowFlex", view = "side", position = "Standing, elbow at your side", side = "", targetAngle = 130, tolerance = 10, safetyMax = 150, sets = 1, restSeconds = 30, baseReps = 8, reps = 8, stage = 1, cue = "Bend your elbow and bring your hand up" },
                    new ExerciseDef { id = 3, code = "kneeExt", name = "Seated knee extension", joint = "Knee", measure = "kneeExt", view = "side", position = "Sitting tall, knee bent at 90", side = "", targetAngle = 80, tolerance = 10, sets = 1, restSeconds = 30, baseReps = 8, reps = 8, stage = 1, cue = "Sit tall and straighten your knee slowly" },
                }
            };
        }
    }
}
