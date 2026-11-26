using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>The "Joint Angle" logo (human choice B, 2026-11-19): mark file, name, and the app icon.</summary>
    public class LogoTests
    {
        [Test]
        public void LogoMark_IsInResources_AndSquare()
        {
            var tex = Resources.Load<Texture2D>(MenuController.LogoMarkResource);
            Assert.IsNotNull(tex, "Resources/" + MenuController.LogoMarkResource);
            Assert.AreEqual(tex.width, tex.height);
        }

        [Test]
        public void LogoName_IsTheraQuest_InTwoColours()
        {
            var plain = System.Text.RegularExpressions.Regex.Replace(MenuController.LogoText, "<[^>]+>", "");
            Assert.AreEqual("TheraQuest", plain);
            StringAssert.Contains(UIKit.HexTeal, MenuController.LogoText);
        }

        [Test]
        public void LogoName_UsesTheCartoonDisplayFont()
        {
            Assert.GreaterOrEqual(MenuController.LogoNameSize, UIKit.DisplaySize);
            Assert.AreEqual(UIKit.DisplayFont, UIKit.FontFor(MenuController.LogoNameSize, FontStyle.Bold));
        }

        [Test]
        public void AppIcon_IsTheLogo()
        {
            var icons = UnityEditor.PlayerSettings.GetIcons(UnityEditor.Build.NamedBuildTarget.Unknown, UnityEditor.IconKind.Any);
            Assert.IsTrue(icons.Length > 0 && icons[0] != null, "default app icon set");
            StringAssert.EndsWith("TheraQuestIcon.png", UnityEditor.AssetDatabase.GetAssetPath(icons[0]));
        }
    }
}
