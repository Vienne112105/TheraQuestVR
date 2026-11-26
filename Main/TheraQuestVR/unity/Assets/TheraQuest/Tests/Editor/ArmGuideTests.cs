using NUnit.Framework;

namespace TheraQuest.Tests
{
    /// <summary>The arm hologram sits 1.5 in forward so the patient strains the neck less looking at it (2026-11-19).</summary>
    public class ArmGuideTests
    {
        [Test]
        public void ArmGuide_Is1Point5InchesForwardOfTheShoulderLine()
        {
            var arm = FirstPersonMath.Limbs("shoulderFlex", 1, 0f)[0];
            Assert.AreEqual(-0.06f + 0.0381f, arm.root.z, 0.0005f);
        }

        [Test]
        public void LegGuide_IsNotMoved()
        {
            var leg = FirstPersonMath.Limbs("slr", 1, 0f)[0];
            Assert.AreEqual(-0.06f, leg.root.z, 0.0005f);
        }
    }
}
