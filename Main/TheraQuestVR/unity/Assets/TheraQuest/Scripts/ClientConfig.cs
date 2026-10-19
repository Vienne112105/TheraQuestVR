using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// Clinic settings for a built player, which has no Inspector (M4.3). Read in this order:
    ///   1. command line: TheraQuestVR.exe -patient P-002 -server http://127.0.0.1:8000
    ///   2. config.json in Application.persistentDataPath (written by the therapist page in the menu)
    ///   3. the Inspector values on ApiClient
    /// The therapist page is protected by a 4-digit PIN, stored only as a SHA-256 hash.
    /// </summary>
    [Serializable]
    public class ClientConfig
    {
        public string patientCode = "";
        public string serverUrl = "";
        public string pinHash = "";

        public static string PathOnDisk => Path.Combine(Application.persistentDataPath, "config.json");

        static ClientConfig loaded;
        public static ClientConfig Current => loaded ?? (loaded = Load());

        static ClientConfig Load()
        {
            try
            {
                if (File.Exists(PathOnDisk))
                    return JsonUtility.FromJson<ClientConfig>(File.ReadAllText(PathOnDisk)) ?? new ClientConfig();
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[TheraQuest] Ignoring unreadable {PathOnDisk}: {e.Message}");
            }
            return new ClientConfig();
        }

        public void Save()
        {
            try
            {
                string tmp = PathOnDisk + ".tmp";
                File.WriteAllText(tmp, JsonUtility.ToJson(this, true));
                if (File.Exists(PathOnDisk)) File.Delete(PathOnDisk);
                File.Move(tmp, PathOnDisk);
            }
            catch (IOException e)
            {
                Debug.LogError($"[TheraQuest] Could not save {PathOnDisk}: {e.Message}");
            }
        }

        /// <summary>Value of a "-name value" command-line argument, or null.</summary>
        public static string Arg(string name)
        {
            var args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length - 1; i++)
                if (string.Equals(args[i], "-" + name, StringComparison.OrdinalIgnoreCase)) return args[i + 1];
            return null;
        }

        public static string NormalizeCode(string code) => (code ?? "").Trim().ToUpperInvariant();

        public bool HasPin => !string.IsNullOrEmpty(pinHash);
        public bool CheckPin(string pin) => HasPin && pinHash == Hash(pin);
        public void SetPin(string pin) { pinHash = Hash(pin); Save(); }

        static string Hash(string pin)
        {
            using (var sha = SHA256.Create())
            {
                var bytes = sha.ComputeHash(Encoding.UTF8.GetBytes("TheraQuest-PIN:" + pin));
                var sb = new StringBuilder();
                foreach (var b in bytes) sb.Append(b.ToString("x2"));
                return sb.ToString();
            }
        }
    }
}
