using System.IO;
using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>
    /// M8.2 regression: the coach repaints once made both coaches' eyes disappear, because the face shares picture cells
    /// with the clothes and hair. The cells that hold the eyes, face and hair must stay exactly as the Little Guys
    /// pack made them; only the shirt and trousers cells may differ.
    /// </summary>
    public class CoachFaceTests
    {
        const string Pack = "Assets/LuceedStudio/Character Lab/Little Guys/Little Guys - Free Sample/";

        static Texture2D Load(string path)
        {
            var t = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            Assert.IsTrue(t.LoadImage(File.ReadAllBytes(path)), path);
            return t;
        }

        // (column, row) of the 3x3 cells that must not change: row 0 is the top of the picture
        static readonly (int, int)[] Protected = { (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2) };

        [TestCase("Woman/Free Woman/Textures/T_FreeWoman.png", "Assets/TheraQuest/Resources/CoachTextures/coach_woman.png")]
        [TestCase("Man/Free Man/Textures/T_FreeMan.png", "Assets/TheraQuest/Resources/CoachTextures/coach_man.png")]
        public void FaceHairAndEyeCells_AreUntouched(string packFile, string repaint)
        {
            var o = Load(Pack + packFile); var n = Load(repaint);
            Assert.AreEqual(o.width, n.width); Assert.AreEqual(o.height, n.height);
            int cell = o.width / 3, changed = 0;
            var po = o.GetPixels32(); var pn = n.GetPixels32();
            // The picture is cut into 3 x 3 cells of 341 pixels, the last row and column take the extra pixel.
            // Texture2D rows run from the bottom, so the picture's row is height - 1 - y.
            for (int y = 0; y < o.height; y++)
                for (int x = 0; x < o.width; x++)
                {
                    int cx = Mathf.Min(x / cell, 2), cy = Mathf.Min((o.height - 1 - y) / cell, 2);
                    if (System.Array.IndexOf(Protected, (cx, cy)) < 0) continue;
                    var a = po[y * o.width + x]; var b = pn[y * n.width + x];
                    if (a.r != b.r || a.g != b.g || a.b != b.b) changed++;
                }
            Assert.AreEqual(0, changed, changed + " pixels changed in the cells that hold the face, hair or eyes");
        }
    }
}
