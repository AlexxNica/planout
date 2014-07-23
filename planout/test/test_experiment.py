# Copyright (c) 2014, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import json
import unittest

from planout.experiment import Experiment
from planout.interpreter import Interpreter
from planout.ops.random import UniformChoice

global_log = []
class ExperimentTest(unittest.TestCase):

  def experiment_tester(self, exp_class):
    global global_log
    global_log = []

    e = exp_class(i=42)
    e.set_overrides({'bar': 42})
    params = e.get_params()

    self.assertTrue('foo' in params)
    self.assertEqual(params['foo'], 'b')

    # test to make sure overrides work correctly
    self.assertEqual(params['bar'], 42)

    # log should only have one entry, and should contain i as an input
    # and foo and bar as parameters
    self.assertEqual(len(global_log), 1)
    self.validate_log(params, {
      'inputs': {'i': None},
      'params': {'foo': None, 'bar': None}
    })

  def validate_log(self, blob, expected_fields):
    # Expected field is a dictionary containing all of the expected keys
    # in the expected structure. Key values are ignored.
    blob = global_log[0]
    for field in expected_fields:
      self.assertTrue(field in blob)
      if expected_fields[field] is dict:
        self.assertTrue(self.validate_log(
          blob[field],
          expected_fields[field]
          ))
      else:
        self.assertTrue(field in blob)

  def test_vanilla_experiment(self):
    class TestVanillaExperiment(Experiment):
      def configure_logger(self): pass
      def log(self, stuff): global_log.append(stuff)
      def previously_logged(self): pass

      def setup(self):
        self.name = 'test_name'

      def assign(self, params, i):
        params.foo = UniformChoice(choices=['a', 'b'], unit=i)

    self.experiment_tester(TestVanillaExperiment)

  # makes sure assignment only happens once
  def test_single_assignment(self):
    class TestSingleAssignment(Experiment):
      def configure_logger(self): pass
      def log(self, stuff): global_log.append(stuff)
      def previously_logged(self): pass

      def setup(self):
        self.name = 'test_name'

      def assign(self, params, i, counter):
        params.foo = UniformChoice(choices=['a', 'b'], unit=i)
        counter['count'] = counter.get('count', 0) + 1

    assignment_count = {'count': 0}
    e = TestSingleAssignment(i=10, counter=assignment_count)
    self.assertEqual(assignment_count['count'], 0)
    e.get('foo')
    self.assertEqual(assignment_count['count'], 1)
    e.get('foo')
    self.assertEqual(assignment_count['count'], 1)



  def test_interpreted_experiment(self):
    class TestInterpretedExperiment(Experiment):
      def configure_logger(self): pass
      def log(self, stuff): global_log.append(stuff)
      def previously_logged(self): pass

      def setup(self):
        self.name = 'test_name'

      def assign(self, params, **kwargs):
        compiled = json.loads("""
          {"op":"seq",
           "seq": [
            {"op":"set",
             "var":"foo",
             "value":{
               "choices":["a","b"],
               "op":"uniformChoice",
               "unit": {"op": "get", "var": "i"}
               }
            },
            {"op":"set",
             "var":"bar",
             "value": 41
            }
           ]}
        """)
        proc = Interpreter(compiled, self.salt, kwargs, params)
        params.update(proc.get_params())

    self.experiment_tester(TestInterpretedExperiment)


if __name__ == '__main__':
  unittest.main()
