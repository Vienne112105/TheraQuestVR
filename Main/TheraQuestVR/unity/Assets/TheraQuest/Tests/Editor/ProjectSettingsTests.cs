using NUnit.Framework;
using UnityEngine;

namespace TheraQuest.Tests
{
    /// <summary>The Unity company name decides the data folder (M7.4); it must not stay at the default.</summary>
    public class ProjectSettingsTests
    {
        [Test]
        public void CompanyName_IsNotDefault()
        {
            Assert.AreEqual("TheraQuest", Application.companyName);
        }

        [TestCase("webcam", true, "")]
        [TestCase("keyboard", false, "Practice: not counted")]
        [TestCase("simulated", false, "Practice: not counted")]
        [TestCase("", false, "Practice: not counted")]
        public void PracticeLine_OnlyForNonWebcam(string source, bool counted, string line)
        {
            Assert.AreEqual(counted, ProgressViews.IsCounted(source));
            Assert.AreEqual(line, ProgressViews.PracticeLine(source));
        }
    }
}
