import pytest
import tempfile

from sire.legacy.IO import GroTop

import BioSimSpace.Sandpit.Exscientia as BSS

from tests.Sandpit.Exscientia.conftest import has_gromacs


@pytest.fixture(scope="module")
def system():
    return BSS.IO.readMolecules(
        BSS.IO.expand(BSS.tutorialUrl(), ["ala_xtal_water.gro", "ala_xtal_water.top"])
    )


@pytest.mark.parametrize("match_water", [True, False])
@pytest.mark.skipif(not has_gromacs, reason="Requires GROMACS to be installed")
def test_crystal_water(system, match_water):
    """
    Test that user defined crystal waters can be preserved during
    solvation and on write to GroTop format.
    """

    # Store the number of crystal waters.
    if match_water:
        num_matches = 0
    else:
        num_matches = len(system.search("resname COF").molecules())

    # Create the box parameters.
    box, angles = BSS.Box.cubic(3 * BSS.Units.Length.nanometer)

    # Create the solvated system.
    solvated = BSS.Solvent.tip3p(system, box, angles, match_water=match_water)

    # Search for the crystal waters in the solvated system.
    try:
        num_cof = len(solvated.search("resname COF").molecules())
    except:
        num_cof = 0

    # Check that the number of crystal waters is as expected.
    assert num_cof == num_matches

    # Create a temporary working directory.
    tmp_dir = tempfile.TemporaryDirectory()
    tmp_path = tmp_dir.name

    # Write to GroTop format.
    BSS.IO.saveMolecules(
        f"{tmp_path}/test", solvated, "grotop", match_water=match_water
    )

    # Initialise the number of crystal waters.
    num_cof = 0

    # Read back in.
    with open(f"{tmp_path}/test.top", "r") as f:
        for line in f:
            if "COF" in line:
                num_cof = int(line.strip().split()[1])
                break

    # Make sure the correct number of crystal waters are present.
    assert num_cof == num_matches

    if not match_water:
        # Write to GroTop format, replacing the water topology.
        BSS.IO.saveMolecules(f"{tmp_path}/test", solvated, "grotop", match_water=True)

        # Initialise the number of crystal waters.
        num_cof = 0

        # Read back in.
        with open(f"{tmp_path}/test.top", "r") as f:
            for line in f:
                if "COF" in line:
                    num_cof = int(line.strip().split()[1])
                    break

        # Make sure there are no crystal waters in the file.
        assert num_cof == 0
