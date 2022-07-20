"""Test module semver
"""

import random
import string

from witch_ver import semver

from tests import base


class TestSemVer(base.TestBase):
  """Test SemVer class
  """

  def test_init(self):
    major = random.randint(0, 100)
    minor = random.randint(0, 100)
    patch = random.randint(0, 100)

    self.assertRaises(TypeError, semver.SemVer)
    self.assertRaises(TypeError, semver.SemVer, major=major, minor=minor)
    self.assertRaises(TypeError, semver.SemVer, minor=minor, patch=patch)
    self.assertRaises(TypeError, semver.SemVer, major=major, patch=patch)

    v = semver.SemVer(major=major, minor=minor, patch=patch)
    self.assertEqual(major, v.major)
    self.assertEqual(minor, v.minor)
    self.assertEqual(patch, v.patch)
    self.assertListEqual([], v.prerelease_list)
    self.assertListEqual([], v.build_list)

    s = f"{major}.{minor}"
    self.assertRaises(ValueError, semver.SemVer, string=s)

    s = f"{major}.{minor}.{patch}"
    v = semver.SemVer(string=s)
    self.assertEqual(major, v.major)
    self.assertEqual(minor, v.minor)
    self.assertEqual(patch, v.patch)
    self.assertListEqual([], v.prerelease_list)
    self.assertListEqual([], v.build_list)

    ###### Prerelease tagging #####

    prerelease = str(random.randint(0, 1000))

    v = semver.SemVer(major=major,
                      minor=minor,
                      patch=patch,
                      prerelease=prerelease)
    self.assertEqual(major, v.major)
    self.assertEqual(minor, v.minor)
    self.assertEqual(patch, v.patch)
    self.assertEqual(prerelease, v.prerelease)
    self.assertListEqual([], v.build_list)

    prerelease = f"{random.getrandbits(64):X}-" + string.ascii_letters

    v = semver.SemVer(major=major,
                      minor=minor,
                      patch=patch,
                      prerelease=prerelease)
    self.assertEqual(major, v.major)
    self.assertEqual(minor, v.minor)
    self.assertEqual(patch, v.patch)
    self.assertEqual(prerelease, v.prerelease)
    self.assertListEqual([], v.build_list)

    s = f"{major}.{minor}.{patch}-{prerelease}"
    v = semver.SemVer(string=s)
    self.assertEqual(major, v.major)
    self.assertEqual(minor, v.minor)
    self.assertEqual(patch, v.patch)
    self.assertEqual(prerelease, v.prerelease)
    self.assertListEqual([], v.build_list)

    s = f"{major}.{minor}.{patch}-"
    self.assertRaises(ValueError, semver.SemVer, string=s)

    s = f"{major}.{minor}.{patch}-01"
    self.assertRaises(ValueError, semver.SemVer, string=s)

    self.assertRaises(ValueError,
                      semver.SemVer,
                      major=major,
                      minor=minor,
                      patch=patch,
                      prerelease=prerelease + "+")
    self.assertRaises(ValueError,
                      semver.SemVer,
                      major=major,
                      minor=minor,
                      patch=patch,
                      prerelease=[prerelease + "+"])

    prerelease = [prerelease, "0", "RC1", "metadata-here-123"]

    v = semver.SemVer(major=major,
                      minor=minor,
                      patch=patch,
                      prerelease=[prerelease[0], ".".join(prerelease[1:])])
    self.assertEqual(major, v.major)
    self.assertEqual(minor, v.minor)
    self.assertEqual(patch, v.patch)
    self.assertListEqual(prerelease, v.prerelease_list)
    self.assertListEqual([], v.build_list)

    v = semver.SemVer(major=major,
                      minor=minor,
                      patch=patch,
                      prerelease=".".join(prerelease))
    self.assertEqual(major, v.major)
    self.assertEqual(minor, v.minor)
    self.assertEqual(patch, v.patch)
    self.assertListEqual(prerelease, v.prerelease_list)
    self.assertListEqual([], v.build_list)

    ###### Build metadata tagging #####

    build = f"{random.getrandbits(64):X}-" + string.ascii_letters

    v = semver.SemVer(major=major, minor=minor, patch=patch, build=build)
    self.assertEqual(major, v.major)
    self.assertEqual(minor, v.minor)
    self.assertEqual(patch, v.patch)
    self.assertListEqual([], v.prerelease_list)
    self.assertEqual(build, v.build)

    s = f"{major}.{minor}.{patch}+{build}"
    v = semver.SemVer(string=s)
    self.assertEqual(major, v.major)
    self.assertEqual(minor, v.minor)
    self.assertEqual(patch, v.patch)
    self.assertListEqual([], v.prerelease_list)
    self.assertEqual(build, v.build)

    s = f"{major}.{minor}.{patch}+"
    self.assertRaises(ValueError, semver.SemVer, string=s)

    s = f"{major}.{minor}.{patch}+{build}+{build}"
    self.assertRaises(ValueError, semver.SemVer, string=s)

    self.assertRaises(ValueError,
                      semver.SemVer,
                      major=major,
                      minor=minor,
                      patch=patch,
                      build=build + "+")
    self.assertRaises(ValueError,
                      semver.SemVer,
                      major=major,
                      minor=minor,
                      patch=patch,
                      build=[build + "+"])

    build = [build, "beta", "RC1", "metadata-here-123"]

    v = semver.SemVer(major=major,
                      minor=minor,
                      patch=patch,
                      build=[build[0], ".".join(build[1:])])
    self.assertEqual(major, v.major)
    self.assertEqual(minor, v.minor)
    self.assertEqual(patch, v.patch)
    self.assertListEqual([], v.prerelease_list)
    self.assertListEqual(build, v.build_list)

    v = semver.SemVer(major=major,
                      minor=minor,
                      patch=patch,
                      build=".".join(build))
    self.assertEqual(major, v.major)
    self.assertEqual(minor, v.minor)
    self.assertEqual(patch, v.patch)
    self.assertListEqual([], v.prerelease_list)
    self.assertListEqual(build, v.build_list)

    ###### Both tagging #####

    v = semver.SemVer(major=major,
                      minor=minor,
                      patch=patch,
                      prerelease=".".join(prerelease),
                      build=".".join(build))
    self.assertEqual(major, v.major)
    self.assertEqual(minor, v.minor)
    self.assertEqual(patch, v.patch)
    self.assertListEqual(prerelease, v.prerelease_list)
    self.assertListEqual(build, v.build_list)

  def test_equality(self):
    major = random.randint(0, 100)
    minor = random.randint(0, 100)
    patch = random.randint(0, 100)
    prerelease = f"{random.getrandbits(64):X}.alpha"
    build = f"{random.getrandbits(64):X}.2022"

    v = semver.SemVer(major=major,
                      minor=minor,
                      patch=patch,
                      prerelease=prerelease,
                      build=build)

    self.assertRaises(TypeError, v.__eq__, None)

    s = f"{major}.{minor}.{patch}-{prerelease}+{build}"

    self.assertEqual(v, s)
    self.assertEqual(s, v)
    self.assertEqual(v, semver.SemVer(s))

    s = f"{major}.{minor}.{patch}-{prerelease}+{build}.extra"
    self.assertNotEqual(v, semver.SemVer(s))

    s = f"{major}.{minor}.{patch}-{prerelease}"
    self.assertNotEqual(v, semver.SemVer(s))

    s = f"{major}.{minor}.{patch}-{prerelease}.extra"
    self.assertNotEqual(v, semver.SemVer(s))

    s = f"{major}.{minor}.{patch}"
    self.assertNotEqual(v, semver.SemVer(s))

    s = f"{major}.{minor}.1{patch}"
    self.assertNotEqual(v, semver.SemVer(s))

    s = f"{major}.1{minor}.{patch}"
    self.assertNotEqual(v, semver.SemVer(s))

    s = f"1{major}.{minor}.{patch}"
    self.assertNotEqual(v, semver.SemVer(s))

  def test_compare(self):
    v = semver.SemVer("2.1.1")

    self.assertRaises(TypeError, v.__gt__, None)

    self.assertGreater(v, semver.SemVer("1.0.0"))
    self.assertGreater(v, "1.0.0")
    self.assertGreater(v, "2.0.0")
    self.assertGreater(v, "2.1.0")
    self.assertGreater(v, "2.1.1-alpha")

    self.assertLessEqual(v, str(v))
    self.assertGreaterEqual(v, str(v))

    v = semver.SemVer("2.1.1-beta.10")
    self.assertGreater(v, "2.1.1-alpha")
    self.assertGreater(v, "2.1.1-beta.2")
    self.assertGreater(v, "2.1.1-99999")
    self.assertLessEqual(v, "2.1.1-beta.extra")
    self.assertGreater(v, "2.1.1-beta.10.extra")

    self.assertLess(v, "2.1.1-beta.extra")

  def test_str(self):
    major = random.randint(0, 100)
    minor = random.randint(0, 100)
    patch = random.randint(0, 100)
    prerelease = f"{random.getrandbits(64):X}.alpha"
    build = f"{random.getrandbits(64):X}.2022"

    s = f"{major}.{minor}.{patch}-{prerelease}+{build}"

    v = semver.SemVer(s)

    self.assertEqual(str(v), s)

    r = f"<witch_ver.semver.SemVer '{s}'>"
    self.assertEqual(repr(v), r)

  def test_bump(self):
    major = random.randint(0, 100)
    minor = random.randint(0, 100)
    patch = random.randint(0, 100)
    prerelease = f"{random.getrandbits(64):X}.alpha"
    build = f"{random.getrandbits(64):X}.2022"

    s = f"{major}.{minor}.{patch}-{prerelease}+{build}"

    v = semver.SemVer(s)
    v.bump_major()
    self.assertEqual(major + 1, v.major)
    self.assertEqual(0, v.minor)
    self.assertEqual(0, v.patch)
    self.assertListEqual([], v.prerelease_list)
    self.assertListEqual([], v.build_list)

    v.append_prerelease(prerelease)
    v.append_build(build)

    v.bump_patch()
    self.assertEqual(major + 1, v.major)
    self.assertEqual(0, v.minor)
    self.assertEqual(1, v.patch)
    self.assertListEqual([], v.prerelease_list)
    self.assertListEqual([], v.build_list)

    v.append_prerelease(prerelease)
    v.append_build(build)

    v.bump_minor()
    self.assertEqual(major + 1, v.major)
    self.assertEqual(1, v.minor)
    self.assertEqual(0, v.patch)
    self.assertListEqual([], v.prerelease_list)
    self.assertListEqual([], v.build_list)
