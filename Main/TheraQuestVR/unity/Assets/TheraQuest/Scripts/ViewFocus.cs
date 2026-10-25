using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// Auto-focus on the exercise (requested 2026-10-26). On the laptop, at every exercise's get-ready card the
    /// camera eases forward and turns to frame the coach doing that exercise: closer for small motions, wider for
    /// standing ones, tilted down for exercises on the treatment table. It then stays there for the exercise.
    /// In the headset the view is never moved on its own (motion sickness); SessionManager re-centers instead.
    /// Put it on the camera Rig (SessionManager adds it at runtime).
    /// </summary>
    public class ViewFocus : MonoBehaviour
    {
        public HeadTracking head;
        public PlayerMover mover;
        [Tooltip("Seconds to wait before measuring the coach, so its new pose (and the 'pop') has settled.")]
        public float settleSeconds = 0.45f;
        public float easeSeconds = 1.2f;
        [Tooltip("Room left around the coach, as a share of its size.")]
        public float margin = 1.25f;
        [Tooltip("Extra height above a standing coach for raised arms.")]
        public float headroom = 0.35f;
        public float minDistance = 1.3f, maxDistance = 4.5f;

        Transform target;
        float wait, t = -1f;
        Vector3 fromPos, toPos;
        Quaternion fromRot, toRot;
        float fromPitch, toPitch;

        /// <summary>Frame <paramref name="coach"/> once its pose has settled.</summary>
        public void FocusOn(Transform coach)
        {
            target = coach;
            wait = settleSeconds;
            t = -1f;
        }

        /// <summary>Stop any move in progress (e.g. the player was sent back to the exercise spot).</summary>
        public void Release()
        {
            target = null;
            t = -1f;
        }

        void Update()
        {
            if (head != null && head.HeadsetActive) { Release(); return; }
            float dt = Time.deltaTime;   // freezes while paused
            if (target != null && t < 0f)
            {
                if ((wait -= dt) > 0f) return;
                if (!Plan()) { Release(); return; }
                t = 0f;
            }
            if (t < 0f) return;
            t = Mathf.Min(1f, t + dt / Mathf.Max(0.01f, easeSeconds));
            float k = t * t * (3f - 2f * t);   // smoothstep
            transform.SetPositionAndRotation(Vector3.Lerp(fromPos, toPos, k), Quaternion.Slerp(fromRot, toRot, k));
            if (head != null) head.desktopPitch = Mathf.Lerp(fromPitch, toPitch, k);
            if (t >= 1f) Release();
        }

        /// <summary>Works out where the rig should stand to frame the coach. False when there is nothing to frame.</summary>
        bool Plan()
        {
            if (!CoachBounds(target, out var b)) return false;
            var cam = Camera.main;
            if (cam == null) return false;
            float eye = head != null ? head.desktopEyeHeight : 1.55f;
            var camPos = transform.position + Vector3.up * eye;
            bool standing = b.size.y > 1.2f;
            var pose = Frame(camPos, eye, b, standing ? headroom : 0f, cam.fieldOfView, cam.aspect, margin, minDistance, maxDistance);
            fromPos = transform.position;
            fromRot = transform.rotation;
            fromPitch = head != null ? head.desktopPitch : 0f;
            toPos = ClampToRoom(pose.rigPosition);
            toRot = Quaternion.Euler(0f, pose.yaw, 0f);
            toPitch = pose.pitch;
            return true;
        }

        Vector3 ClampToRoom(Vector3 p)
        {
            if (mover == null) return p;
            p.x = Mathf.Clamp(p.x, mover.roomMin.x, mover.roomMax.x);
            p.z = Mathf.Clamp(p.z, mover.roomMin.y, mover.roomMax.y);
            return p;
        }

        /// <summary>Bounds of everything visible on the coach (character, treatment table, guides).</summary>
        static bool CoachBounds(Transform root, out Bounds b)
        {
            b = default;
            bool any = false;
            if (root == null) return false;
            foreach (var r in root.GetComponentsInChildren<Renderer>())
            {
                if (!r.enabled || !r.gameObject.activeInHierarchy || r is ParticleSystemRenderer) continue;
                if (!any) { b = r.bounds; any = true; }
                else b.Encapsulate(r.bounds);
            }
            return any;
        }

        public struct RigPose { public Vector3 rigPosition; public float yaw, pitch, distance; }

        /// <summary>
        /// Pure framing math (unit tested). The camera stays at eye height and moves along the floor on the line
        /// from where it is now to the coach, far enough that the coach (plus headroom) fits the view with margin.
        /// </summary>
        public static RigPose Frame(Vector3 camPos, float eyeHeight, Bounds coach, float headroom, float vFovDeg, float aspect,
                                    float margin, float minDistance, float maxDistance)
        {
            var center = coach.center + Vector3.up * headroom * 0.5f;
            float halfH = coach.extents.y + headroom * 0.5f;
            float halfW = Mathf.Max(coach.extents.x, coach.extents.z);
            float tanV = Mathf.Tan(vFovDeg * 0.5f * Mathf.Deg2Rad);
            float tanH = tanV * Mathf.Max(0.1f, aspect);
            // Distance to the coach's centre so both its height and width fit, plus half its depth (it has volume)
            float d = Mathf.Max(halfH / tanV, halfW / tanH) * margin + Mathf.Min(coach.extents.x, coach.extents.z);
            d = Mathf.Clamp(d, minDistance, maxDistance);

            var flat = new Vector3(center.x - camPos.x, 0f, center.z - camPos.z);
            var dir = flat.sqrMagnitude > 1e-4f ? flat.normalized : Vector3.forward;
            var camTarget = new Vector3(center.x, camPos.y, center.z) - dir * d;
            float pitch = Mathf.Atan2(camTarget.y - center.y, d) * Mathf.Rad2Deg;   // positive = look down
            return new RigPose
            {
                rigPosition = camTarget - Vector3.up * eyeHeight,
                yaw = Mathf.Atan2(dir.x, dir.z) * Mathf.Rad2Deg,
                pitch = Mathf.Clamp(pitch, -30f, 45f),
                distance = d,
            };
        }
    }
}
