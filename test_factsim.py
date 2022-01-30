import unittest
import FactSim

class TestFactsim(unittest.TestCase):
      
    def test_opbenBp(self):
        path = "./tests/00-basic_test.bp"
        f = FactSim.Factsimcmd(filename=path)
        #print(f.Entities)
        self.assertEqual(len(f.Entities), 4)

if __name__ == '__main__':
    unittest.main()
