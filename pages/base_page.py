from utils.waits import build_wait

class BasePage:
    def __init__(self, driver, timeout=15):
        self.driver = driver
        self.wait = build_wait(driver, timeout)

    @property
    def d(self):
        return self.driver
