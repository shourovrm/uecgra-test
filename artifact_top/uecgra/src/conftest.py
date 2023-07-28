import pytest
import sys
import os

# Insert the top level directory to PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))) )
# Some UE components are Verilog blackboxes whose source file paths use
# environment variable $RGALS_TOP
assert "RGALS_TOP" in os.environ, "You need to store the path of uecgra-src repo into RGALS_TOP!"

def pytest_addoption(parser):
  parser.addoption( "--clock-time", action="store", default="1.33" )
  parser.addoption( "--fifo-depth", action="store", default=2, choices=[1, 2, 4, 8, 16], type=int )
  parser.addoption( "--fifo-latency", action="store", default="0", choices=["0", "1", "2", "3"] )
  # Do we want to make the fast clock slower than default (e.g., 2.5 : 3 : 9 rather than 2 : 3 : 9)?
  parser.addoption( "--slow-fast-clock", action="store_true" )
  parser.addoption( "--test-verilog", action="store", default='', nargs='?', const='zeros', choices=[ '', 'zeros', 'ones', 'rand' ],
                    help="run verilog translation, " )
  parser.addoption( "--dump-vcd", action="store_true",
                    help="dump vcd for each test" )

@pytest.fixture
def test_verilog(request):
  """Test Verilog translation rather than python."""
  return request.config.option.test_verilog

@pytest.fixture
def dump_vcd(request):
  """Dump VCD for each test."""
  if request.config.option.dump_vcd:
    test_module = request.module.__name__
    test_name   = request.node.name
    return '{}.{}.vcd'.format( test_module, test_name )
  else:
    return ''

def pytest_cmdline_preparse(config, args):
  """Don't write *.pyc and __pycache__ files."""
  import sys
  sys.dont_write_bytecode = True

def pytest_runtest_setup(item):
  test_verilog = item.config.option.test_verilog
  if test_verilog and 'test_verilog' not in item.funcargnames:
    pytest.skip("ignoring non-Verilog tests")
