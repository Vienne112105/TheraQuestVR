using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// Auto-focus on the moving limb (first-person view, M5.8). On the laptop the patient can't look around during an
    /// exercise, so the view eases from where it is to the limb's movement, with a wider lens to fit more of it. The
    /// camera only turns: it stays at the eyes. In the headset the view is never moved on its own (motion sickness);
    /// the patient looks at the limb themself. Put it on the camera Rig (SessionManager adds it at runtime).
    /// </summary>
    public class ViewFocus : MonoBehaviour
    {
        public HeadTracking head;
        public float easeSeconds = 1.2f;
        [Tooltip("Lens during exercises on the laptop: first person needs more of the view around the body.")]
        public float exerciseFov = 72f;

        float t = -1f, fromYaw, toYaw, fromPitch, toPitch, normalFov = -1f;

        /// <summary>Turn the view to frame a movement from the start point to the target (room positions).</summary>
        public void AimAt(Vector3 eye, Vector3 start, Vector3 goal)
        {
            FirstPersonMath.Aim(start - eye, goal - eye, out toYaw, out toPitch);
            Begin();
        }

        /// <summary>Turn the view straight ahead, a little down (the limb is seen in the side mirror instead).</summary>
        public void AimAhead()
        {
            toYaw = 0f;
            toPitch = 8f;
            Begin();
        }

        void Begin()
        {
            fromYaw = transform.eulerAngles.y;
            fromPitch = head != null ? head.desktopPitch : 0f;
            t = 0f;
        }

        /// <summary>Stop any move in progress (e.g. the player was sent back to the exercise spot).</summary>
        public void Release() => t = -1f;

        /// <summary>The wider lens during exercises, the scene's own otherwise. The headset ignores it.</summary>
        public void Wide(bool wide)
        {
            var cam = Camera.main;
            if (cam == null || cam.stereoEnabled) return;
            if (normalFov < 0f) normalFov = cam.fieldOfView;
            cam.fieldOfView = wide ? exerciseFov : normalFov;
        }

        void Update()
        {
            if (head != null && head.HeadsetActive) { Release(); return; }
            if (t < 0f) return;
            t = Mathf.Min(1f, t + Time.deltaTime / Mathf.Max(0.01f, easeSeconds));   // freezes while paused
            float k = t * t * (3f - 2f * t);   // smoothstep
            transform.rotation = Quaternion.Euler(0f, Mathf.LerpAngle(fromYaw, toYaw, k), 0f);
            if (head != null) head.desktopPitch = Mathf.Lerp(fromPitch, toPitch, k);
            if (t >= 1f) Release();
        }
    }
}
