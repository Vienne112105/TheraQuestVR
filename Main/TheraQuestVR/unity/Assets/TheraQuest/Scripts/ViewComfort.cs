using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// The comfortable field of view for panels in the headset (M8.4, VRClinicExperience invariant): angles from the
    /// view direction the panels are placed in front of. A panel's middle sits where the eyes reach with a small head
    /// turn; its corners stay where a comfortable head turn reaches, never high up, and not far down. Pure, unit tested.
    /// </summary>
    public static class ViewComfort
    {
        /// <summary>Degrees sideways for a panel's centre (comfortable head turn about 30 degrees, plus a little eye turn).</summary>
        public const float MaxCentreYaw = 35f;
        /// <summary>Degrees sideways for any corner (comfortable head turn plus comfortable eye turn).</summary>
        public const float MaxYaw = 55f;
        /// <summary>Degrees up and down for any corner (looking up tires the neck sooner than looking down).</summary>
        public const float MaxUp = 20f, MaxDown = 40f;

        /// <summary>Yaw (right +) and pitch (up +) in degrees of a point in the view's frame (+Z forward).</summary>
        public static Vector2 Angles(Vector3 p) =>
            new Vector2(Mathf.Atan2(p.x, p.z) * Mathf.Rad2Deg,
                        Mathf.Atan2(p.y, new Vector2(p.x, p.z).magnitude) * Mathf.Rad2Deg);

        /// <summary>The four corners of a panel of size (metres) at centre, turned by yaw degrees about the vertical.</summary>
        public static Vector3[] Corners(Vector3 centre, float yaw, Vector2 size)
        {
            var q = Quaternion.Euler(0f, yaw, 0f);
            Vector3 r = q * Vector3.right * (size.x / 2f), u = Vector3.up * (size.y / 2f);
            return new[] { centre - r - u, centre + r - u, centre + r + u, centre - r + u };
        }

        /// <summary>True when the panel's centre and every corner are inside the limits above.</summary>
        public static bool Comfortable(Vector3 centre, float yaw, Vector2 size)
        {
            if (Mathf.Abs(Angles(centre).x) > MaxCentreYaw) return false;
            foreach (var c in Corners(centre, yaw, size))
            {
                var a = Angles(c);
                if (Mathf.Abs(a.x) > MaxYaw || a.y > MaxUp || a.y < -MaxDown) return false;
            }
            return true;
        }

        /// <summary>True when every corner is inside a camera's view (laptop: the panels are locked to the screen).</summary>
        public static bool InsideView(Vector3 centre, float yaw, Vector2 size, float verticalFov, float aspect)
        {
            float tanV = Mathf.Tan(verticalFov * 0.5f * Mathf.Deg2Rad), tanH = tanV * aspect;
            foreach (var c in Corners(centre, yaw, size))
                if (c.z <= 0f || Mathf.Abs(c.x / c.z) > tanH || Mathf.Abs(c.y / c.z) > tanV) return false;
            return true;
        }
    }
}
