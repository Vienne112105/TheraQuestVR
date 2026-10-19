using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// Receives joint-angle packets from tracker.py over UDP on a background thread.
    /// The newest packet is always available through <see cref="Latest"/>.
    /// Listens on 127.0.0.1 only (DEC-002: tracker and Unity run on the same computer), so other devices
    /// on the network can't inject angles. Turn on listenOnAllInterfaces only for a tracker on another PC.
    /// </summary>
    public class MotionReceiver : MonoBehaviour
    {
        public int port = 5005;
        [Tooltip("Accept packets from other computers (tracker.py --host). Off = this computer only.")]
        public bool listenOnAllInterfaces;

        public MotionPacket Latest { get; private set; }
        public bool IsReceiving => Latest != null && Time.realtimeSinceStartup - lastPacketTime < 1.0f;
        public float PacketsPerSecond { get; private set; }
        /// <summary>Why the receiver isn't listening (e.g. the port is used by another program), or null.</summary>
        public string Problem { get; private set; }

        UdpClient client;
        Thread thread;
        volatile bool running;
        readonly object gate = new object();
        string pendingJson;
        float lastPacketTime = -10f;
        int countThisSecond;
        float secondStart;

        void OnEnable()
        {
            Problem = null;
            try
            {
                var address = listenOnAllInterfaces ? IPAddress.Any : IPAddress.Loopback;
                client = new UdpClient(new IPEndPoint(address, port));
                running = true;
                var socket = client;   // the thread keeps its own reference, so OnDisable can't null it underneath
                thread = new Thread(() => Listen(socket)) { IsBackground = true, Name = "TheraQuest UDP" };
                thread.Start();
                Debug.Log($"[TheraQuest] Listening for tracker on {address}:{port}");
            }
            catch (Exception e)
            {
                Problem = $"UDP port {port} is busy (is another TheraQuest window open?)";
                Debug.LogError($"[TheraQuest] Could not open UDP port {port}: {e.Message}");
            }
        }

        void Listen(UdpClient socket)
        {
            var any = new IPEndPoint(IPAddress.Any, 0);
            while (running)
            {
                try
                {
                    byte[] data = socket.Receive(ref any);
                    string json = Encoding.UTF8.GetString(data);
                    lock (gate) pendingJson = json;
                }
                catch (SocketException) { if (!running) break; }
                catch (ObjectDisposedException) { break; }
            }
        }

        void Update()
        {
            string json = null;
            lock (gate)
            {
                if (pendingJson != null) { json = pendingJson; pendingJson = null; }
            }
            if (json != null)
            {
                try
                {
                    Latest = JsonUtility.FromJson<MotionPacket>(json);
                    lastPacketTime = Time.realtimeSinceStartup;
                    countThisSecond++;
                }
                catch (Exception e) { Debug.LogWarning("[TheraQuest] Bad packet: " + e.Message); }
            }
            if (Time.realtimeSinceStartup - secondStart >= 1f)
            {
                PacketsPerSecond = countThisSecond;
                countThisSecond = 0;
                secondStart = Time.realtimeSinceStartup;
            }
        }

        void OnDisable()
        {
            running = false;
            try { client?.Close(); } catch { }   // unblocks Receive on the thread
            if (thread != null && thread.IsAlive) thread.Join(500);
            thread = null;
            client = null;
        }
    }
}
