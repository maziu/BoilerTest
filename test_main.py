
from modbus_server import Modbus_ControllableServer, Temp
import modbus_server as t

import pytest
import logging
import random
import traceback

log = logging.getLogger(__name__)

class ModbusServer():
    def __init__(self):
        log.setLevel(logging.INFO)
        log.info("Setting up server...")
        self._server = Modbus_ControllableServer("COM3", "Serial")
        self._server.enableTestMode()
        log.info("Done!")

    def __enter__(self):
        return self._server

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
            # return False # uncomment to pass exception through

        log.info("Closing server...")
        self._server.disableTestMode()
        self._server.stop_server()
        log.info("Done!")


@pytest.fixture()
def server():
    with ModbusServer() as s:
        yield s


@pytest.mark.order(0)
def test_self(server):
    log.info("Self-testing test system")
    server.setRegister(t.TestReg.REG_TEST, 0x1234)
    assert 0x1234 == server.getRegister(t.TestReg.REG_TEST)
    server.setRegister(t.TestReg.REG_TEST, 0)
    assert 0 == server.getRegister(t.TestReg.REG_TEST)
    server.setBitInRegister(t.TestReg.REG_TEST, 3)
    assert 0x08 == server.getRegister(t.TestReg.REG_TEST) # 4th bit set
    server.setRegister(t.TestReg.REG_TEST, 0xAAAA)
    server.setBitInRegister(t.TestReg.REG_TEST, 1, False)
    assert 0xAAA8 == server.getRegister(t.TestReg.REG_TEST) # 2nd bit cleared
    server.setRegister(t.TestReg.REG_TEST, 0xAAAA)
    server.clrBitInRegister(t.TestReg.REG_TEST, 1)
    assert 0xAAA8 == server.getRegister(t.TestReg.REG_TEST) # 2nd bit cleared
    assert False == server.getBitInRegister(t.TestReg.REG_TEST, 2)
    assert True == server.getBitInRegister(t.TestReg.REG_TEST, 3)
    server.setRegister(t.TestReg.REG_TEST, 0)
    log.info("Self-test: Temperature types")
    t1 = Temp(123)
    assert (float(t1)) == 12.3
    assert (int(t1)) == 123
    t2 = Temp(15.4)
    assert (float(t2)) == 15.4
    assert (int(t2)) == 154
    assert (1+1) == 2
    

@pytest.mark.order(1)
def test_smoke(server):
    log.info("Smoke test: Connection to PLC enable test mode and check temp setting")
    r = float(random.randint(0, 500))/10
    server.setTemperature(t.TempSensor.TS_3D, r)
    server.waitForUpdate()
    assert (server.getTemperature(t.TempSensor.TS_3D)) == r,  \
            f"Basic get / set temperature test failed, no PLC connection or invalid PLC program"
    server.setRegister(t.HMIWrite.REG_SIM_INPUTS, 0)
    server.waitForUpdate()
    assert (server.getInput(t.Devices_IN.DEVI_BtnCirc) == 0)
    assert (server.getInput(t.Devices_IN.DEVI_BtnLighter) == 0)
    assert (server.getInput(t.Devices_IN.DEVI_PFireplace) == 0)
    assert (server.getInput(t.Devices_IN.DEVI_SigThermostat) == 0)
    server.setInput(t.Devices_IN.DEVI_BtnLighter)
    server.waitForUpdate()
    assert (server.getInput(t.Devices_IN.DEVI_BtnLighter) == 1)
    server.clrInput(t.Devices_IN.DEVI_BtnLighter)
    server.waitForUpdate()
    assert (server.getInput(t.Devices_IN.DEVI_BtnLighter) == 0)

def test_ctrlmode(server):
    log.info("Test: Control mode and manual command from HMI")
    server.setRegister(t.HMIWrite.REG_MODE, 0xFFFF) #Control all from HMI 
    server.setRegister(t.HMIWrite.REG_CMD, 0x0000)
    log.info("Set all outputs OFF")
    server.waitForUpdate()
    log.info("Check results")
    assert server.getRegister(t.HMIRead.REG_DeviceStatus) == 0x0000
    server.waitForUpdate()
    server.setBitInRegister(t.HMIWrite.REG_MODE, t.Devices_OUT.DEVO_Belimo1)
    server.setBitInRegister(t.HMIWrite.REG_CMD, t.Devices_OUT.DEVO_Belimo1)
    log.info("Set belimo to ON")
    server.waitForUpdate()
    log.info("Get results")
    assert server.getBitInRegister(t.HMIRead.REG_DeviceStatus, t.Devices_OUT.DEVO_Belimo1) == 1
    log.info("Get disable all outputs")
    server.setRegister(t.HMIWrite.REG_MODE, 0xFFFF) #Control all from HMI 
    server.setRegister(t.HMIWrite.REG_CMD, 0x0000)
    server.waitForUpdate()
    log.info("Check results")
    assert server.getRegister(t.HMIRead.REG_DeviceStatus) == 0x0000
    server.setRegister(t.HMIWrite.REG_MODE, 0) #Disable HMI control
