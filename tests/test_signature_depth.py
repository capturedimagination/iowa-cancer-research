"""Distribution-level checks for the exact finite-pool simulation."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

SPEC=importlib.util.spec_from_file_location("depth",Path(__file__).resolve().parents[1]/"scripts/simulate_signature_depth.py")
depth=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(depth)


class DepthSamplingTests(unittest.TestCase):
    def test_no_thinning_is_identity(self):
        counts=np.array([[2,3,1],[0,5,5],[10,0,0]])
        self.assertTrue(np.array_equal(depth.thin(counts,np.full(3,10),10,np.random.default_rng(1)),counts))

    def test_hypergeometric_known_expectation(self):
        # E[Y_g] = d*K_g/N, with a remainder category not in the signature.
        counts=np.tile(np.array([2,3,1]),(50000,1))
        result=depth.thin(counts,np.full(50000,10),4,np.random.default_rng(21))
        np.testing.assert_allclose(result.mean(axis=0),[.8,1.2,.4],atol=.015,rtol=0)
        self.assertTrue((result<=counts).all() and (result.sum(axis=1)<=4).all())

    def test_multinomial_negative_covariance(self):
        probabilities=np.tile(np.array([.1,.2,.3]),(100000,1))
        result=depth.multinomial_targets(np.full(100000,10),probabilities,np.random.default_rng(22))
        np.testing.assert_allclose(result.mean(axis=0),[1,2,3],atol=.025,rtol=0)
        # Independent binomial gene draws would wrongly give covariance zero.
        self.assertAlmostEqual(float(np.cov(result.T,bias=True)[0,1]),-.2,delta=.04)

    def test_equal_profile_same_depth_score(self):
        counts=np.array([[2,4,0],[2,4,0]])
        self.assertEqual(depth.score(counts,np.array([10,10]))[0],depth.score(counts,np.array([10,10]))[1])


if __name__=="__main__":unittest.main()
