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
    self.assertEqual(major, v._major)  # pylint: disable=protected-access
    self.assertEqual(minor, v._minor)  # pylint: disable=protected-access
    self.assertEqual(patch, v._patch)  # pylint: disable=protected-access
    self.assertListEqual([], v._prerelease)  # pylint: disable=protected-access
    self.assertListEqual([], v._build)  # pylint: disable=protected-access

    s = f"{major}.{minor}"
    self.assertRaises(ValueError, semver.SemVer, string=s)

    s = f"{major}.{minor}.{patch}"
    v = semver.SemVer(string=s)
    self.assertEqual(major, v._major)  # pylint: disable=protected-access
    self.assertEqual(minor, v._minor)  # pylint: disable=protected-access
    self.assertEqual(patch, v._patch)  # pylint: disable=protected-access
    self.assertListEqual([], v._prerelease)  # pylint: disable=protected-access
    self.assertListEqual([], v._build)  # pylint: disable=protected-access

    ###### Prerelease tagging #####

    prerelease = str(random.randint(0, 1000))

    v = semver.SemVer(major=major,
                      minor=minor,
                      patch=patch,
                      prerelease=prerelease)
    self.assertEqual(major, v._major)  # pylint: disable=protected-access
    self.assertEqual(minor, v._minor)  # pylint: disable=protected-access
    self.assertEqual(patch, v._patch)  # pylint: disable=protected-access
    self.assertListEqual([prerelease], v._prerelease)  # pylint: disable=protected-access
    self.assertListEqual([], v._build)  # pylint: disable=protected-access

    prerelease = f"{random.getrandbits(64):X}-" + string.ascii_letters

    v = semver.SemVer(major=major,
                      minor=minor,
                      patch=patch,
                      prerelease=prerelease)
    self.assertEqual(major, v._major)  # pylint: disable=protected-access
    self.assertEqual(minor, v._minor)  # pylint: disable=protected-access
    self.assertEqual(patch, v._patch)  # pylint: disable=protected-access
    self.assertListEqual([prerelease], v._prerelease)  # pylint: disable=protected-access
    self.assertListEqual([], v._build)  # pylint: disable=protected-access

    s = f"{major}.{minor}.{patch}-{prerelease}"
    v = semver.SemVer(string=s)
    self.assertEqual(major, v._major)  # pylint: disable=protected-access
    self.assertEqual(minor, v._minor)  # pylint: disable=protected-access
    self.assertEqual(patch, v._patch)  # pylint: disable=protected-access
    self.assertListEqual([prerelease], v._prerelease)  # pylint: disable=protected-access
    self.assertListEqual([], v._build)  # pylint: disable=protected-access

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
    self.assertEqual(major, v._major)  # pylint: disable=protected-access
    self.assertEqual(minor, v._minor)  # pylint: disable=protected-access
    self.assertEqual(patch, v._patch)  # pylint: disable=protected-access
    self.assertListEqual(prerelease, v._prerelease)  # pylint: disable=protected-access
    self.assertListEqual([], v._build)  # pylint: disable=protected-access

    v = semver.SemVer(major=major,
                      minor=minor,
                      patch=patch,
                      prerelease=".".join(prerelease))
    self.assertEqual(major, v._major)  # pylint: disable=protected-access
    self.assertEqual(minor, v._minor)  # pylint: disable=protected-access
    self.assertEqual(patch, v._patch)  # pylint: disable=protected-access
    self.assertListEqual(prerelease, v._prerelease)  # pylint: disable=protected-access
    self.assertListEqual([], v._build)  # pylint: disable=protected-access

    ###### Build metadata tagging #####

    build = f"{random.getrandbits(64):X}-" + string.ascii_letters

    v = semver.SemVer(major=major, minor=minor, patch=patch, build=build)
    self.assertEqual(major, v._major)  # pylint: disable=protected-access
    self.assertEqual(minor, v._minor)  # pylint: disable=protected-access
    self.assertEqual(patch, v._patch)  # pylint: disable=protected-access
    self.assertListEqual([], v._prerelease)  # pylint: disable=protected-access
    self.assertListEqual([build], v._build)  # pylint: disable=protected-access

    s = f"{major}.{minor}.{patch}+{build}"
    v = semver.SemVer(string=s)
    self.assertEqual(major, v._major)  # pylint: disable=protected-access
    self.assertEqual(minor, v._minor)  # pylint: disable=protected-access
    self.assertEqual(patch, v._patch)  # pylint: disable=protected-access
    self.assertListEqual([], v._prerelease)  # pylint: disable=protected-access
    self.assertListEqual([build], v._build)  # pylint: disable=protected-access

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
    self.assertEqual(major, v._major)  # pylint: disable=protected-access
    self.assertEqual(minor, v._minor)  # pylint: disable=protected-access
    self.assertEqual(patch, v._patch)  # pylint: disable=protected-access
    self.assertListEqual([], v._prerelease)  # pylint: disable=protected-access
    self.assertListEqual(build, v._build)  # pylint: disable=protected-access

    v = semver.SemVer(major=major,
                      minor=minor,
                      patch=patch,
                      build=".".join(build))
    self.assertEqual(major, v._major)  # pylint: disable=protected-access
    self.assertEqual(minor, v._minor)  # pylint: disable=protected-access
    self.assertEqual(patch, v._patch)  # pylint: disable=protected-access
    self.assertListEqual([], v._prerelease)  # pylint: disable=protected-access
    self.assertListEqual(build, v._build)  # pylint: disable=protected-access
