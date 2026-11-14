using UnityEngine;

namespace TheraQuest
{
    /// <summary>
    /// The one place that says which shaders this project may use (DEC-028: the game renders with URP). Used by the
    /// EditMode tests and by anything that must refuse a Built-in shader.
    /// </summary>
    public static class RenderPipelineCheck
    {
        /// <summary>True for a URP shader, a TextMeshPro shader, a UI shader or one of our own URP shaders.</summary>
        public static bool IsAllowed(Shader s)
        {
            if (s == null) return false;
            string n = s.name;
            return n.StartsWith("Universal Render Pipeline/") || n.StartsWith("TextMeshPro/") || n.StartsWith("Shader Graphs/")
                || n.StartsWith("UI/") || n.StartsWith("Sprites/") || n.StartsWith("TheraQuest/") || n.Contains("URP") || n == "Hidden/InternalErrorShader";
        }
    }
}
