using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.XR;
using UnityEngine.UI;
using UnityEngine.XR.Interaction.Toolkit.Inputs.Readers;
using UnityEngine.XR.Interaction.Toolkit.Interactors;
using UnityEngine.XR.Interaction.Toolkit.Interactors.Visuals;

namespace TheraQuest
{
    /// <summary>
    /// Point-and-press menus in the headset (M10.2, DEC-030). Builds a left and a right controller under the XR Origin's
    /// Camera Offset: each follows the controller's aim pose, shows a simple handle, and carries an XR Interaction Toolkit
    /// ray that only hits UI. The rays show while a menu is open in the headset; the trigger clicks the row pointed at.
    /// Put it on the XR Origin (SessionManager adds it at runtime).
    /// </summary>
    public class ControllerRays : MonoBehaviour
    {
        public const float RayLength = 6f;
        static readonly Color RayColor = new Color(0.36f, 0.78f, 0.86f);

        /// <summary>Whether a menu is open (set by SessionManager).</summary>
        public System.Func<bool> menuOpen = () => false;

        XRRayInteractor left, right;

        public XRRayInteractor Left => left;
        public XRRayInteractor Right => right;

        /// <summary>Builds both controllers under <paramref name="cameraOffset"/>. Safe to call twice.</summary>
        public void Build(Transform cameraOffset)
        {
            if (left != null) return;
            left = MakeController(cameraOffset, "Left", "Controllers/LeftAimPosition", "Controllers/LeftAimRotation", "Controllers/LeftTracked", "Controllers/LeftTrigger");
            right = MakeController(cameraOffset, "Right", "Controllers/RightAimPosition", "Controllers/RightAimRotation", "Controllers/RightTracked", "Controllers/RightTrigger");
            Show(false);
        }

        static XRRayInteractor MakeController(Transform parent, string side, string pos, string rot, string tracked, string trigger)
        {
            var go = new GameObject(side + " Controller");
            go.SetActive(false);   // configure everything before the interactor wakes up
            go.transform.SetParent(parent, false);

            var pose = go.AddComponent<TrackedPoseDriver>();
            pose.positionInput = new InputActionProperty(XrControls.Action(pos));
            pose.rotationInput = new InputActionProperty(XrControls.Action(rot));
            pose.trackingStateInput = new InputActionProperty(XrControls.Action(tracked));
            pose.ignoreTrackingState = true;

            MakeHandle(go.transform);

            var ray = go.AddComponent<XRRayInteractor>();
            ray.handedness = side == "Left" ? InteractorHandedness.Left : InteractorHandedness.Right;
            ray.lineType = XRRayInteractor.LineType.StraightLine;
            ray.maxRaycastDistance = RayLength;
            ray.raycastMask = 0;               // UI only: the room's colliders never stop or grab the ray
            ray.enableUIInteraction = true;
            ray.selectInput = Button(trigger);
            ray.uiPressInput = Button(trigger);
            ray.activateInput = new XRInputButtonReader { inputSourceMode = XRInputButtonReader.InputSourceMode.Unused };

            var line = go.AddComponent<LineRenderer>();
            line.sharedMaterial = new Material(Shader.Find("Universal Render Pipeline/Unlit") ?? Shader.Find("Unlit/Color")) { color = RayColor };
            var visual = go.AddComponent<XRInteractorLineVisual>();
            visual.lineWidth = 0.006f;
            visual.validColorGradient = Solid(RayColor, 1f);
            visual.invalidColorGradient = Solid(RayColor, 0.45f);
            visual.overrideInteractorLineLength = true;
            visual.lineLength = RayLength;
            visual.stopLineAtFirstRaycastHit = true;

            go.SetActive(true);
            return ray;
        }

        // Through a reference, not the action itself: the toolkit turns direct actions off when a ray hides, which would
        // also silence the trigger for InputHelper (same action)
        static XRInputButtonReader Button(string action)
        {
            var reference = InputActionReference.Create(XrControls.Action(action));
            return new XRInputButtonReader
            {
                inputSourceMode = XRInputButtonReader.InputSourceMode.InputActionReference,
                inputActionReferencePerformed = reference,
                inputActionReferenceValue = reference,
            };
        }

        static Gradient Solid(Color c, float alpha)
        {
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(c, 0f), new GradientColorKey(c, 1f) }, new[] { new GradientAlphaKey(alpha, 0f), new GradientAlphaKey(alpha * 0.4f, 1f) });
            return g;
        }

        /// <summary>A simple stand-in for the controller: a short rounded handle with a ring, no collider.</summary>
        static void MakeHandle(Transform parent)
        {
            var handle = Part(PrimitiveType.Capsule, parent, new Vector3(0f, -0.02f, -0.05f), new Vector3(0.035f, 0.05f, 0.035f), Quaternion.Euler(60f, 0f, 0f), UIKit.Navy);
            handle.name = "Handle";
            var ring = Part(PrimitiveType.Cylinder, parent, new Vector3(0f, 0.005f, -0.005f), new Vector3(0.07f, 0.006f, 0.07f), Quaternion.Euler(20f, 0f, 0f), RayColor);
            ring.name = "Ring";
        }

        static GameObject Part(PrimitiveType type, Transform parent, Vector3 pos, Vector3 scale, Quaternion rot, Color color)
        {
            var go = GameObject.CreatePrimitive(type);
            if (Application.isPlaying) Destroy(go.GetComponent<Collider>()); else DestroyImmediate(go.GetComponent<Collider>());
            go.transform.SetParent(parent, false);
            go.transform.SetLocalPositionAndRotation(pos, rot);
            go.transform.localScale = scale;
            var r = go.GetComponent<Renderer>();
            r.sharedMaterial = new Material(Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard")) { color = color };
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            return go;
        }

        void Show(bool on)
        {
            if (left != null && left.gameObject.activeSelf != on) left.gameObject.SetActive(on);
            if (right != null && right.gameObject.activeSelf != on) right.gameObject.SetActive(on);
        }

        void Update()
        {
            bool on = XrMode.InHeadset && menuOpen();
            Show(on);
            InputHelper.RayOnMenu = on && (OnButton(left) || OnButton(right));
        }

        void OnDisable() { InputHelper.RayOnMenu = false; }

        static bool OnButton(XRRayInteractor ray) =>
            ray != null && ray.TryGetCurrentUIRaycastResult(out var hit) && hit.gameObject != null && hit.gameObject.GetComponentInParent<Selectable>() != null;
    }
}
