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
    }
}
