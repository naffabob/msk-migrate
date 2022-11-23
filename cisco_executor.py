import getpass
import telnetlib


class Account:
    def __init__(self, username=None, password=None):
        self.username = username or getpass.getuser()
        self.password = password or getpass.getpass()


class CiscoExecutor:
    PROMPT_LOGIN = b"Username"
    PROMPT_PASSWORD = b"assword"
    PROMPT_CS_ID = b"CISCO"
    PROMPT_CS = [b".*#"]
    PROMPT_CS_SYS_VIEW = [b".*# "]
    PROMPT_ALL = [b".*> $", b".*# $", b".*% $"]
    PROMPT_FAILED_LOGIN = b"% Authentication failed"

    def __init__(self, hostname, account=None, connect=True):
        self.account = account or Account()
        self.hostname = hostname
        self.connected = False
        self._tn = None
        self.eol = b"\r\n"
        if connect:
            self.connect()

    def connect(self):
        self._tn = telnetlib.Telnet(self.hostname)
        self._tn.read_until(self.PROMPT_LOGIN, 2)
        self.run_and_expect(self.account.username, self.PROMPT_PASSWORD, 2)
        index, match, output = self.run_and_expect(self.account.password, self.PROMPT_CS, 2)
        if index == -1:
            self.close()
            raise ConnectionError(f'unable to login {self.hostname}')

        self.run_and_expect("terminal length 0", self.PROMPT_ALL, 1)
        self.connected = True

    def close(self):
        self.connected = False
        self._tn.close()

    def cmd(self, command: str, timer=2) -> str:
        prompt = self.PROMPT_ALL
        self.read_all()
        output = self.run_and_expect(command, prompt, timer)[-1]
        return output.decode('utf8', errors='replace')

    def expect(self, expect, timer=30):
        """Modified telnetlib.except()
        find re_match_object
        Return (-1/id элемента листа, None/match_object, all text/text till up match_object)"""

        if isinstance(expect, list):
            new_except_list = [self.__convert_to_bytes(x) for x in expect]
        else:
            new_except_list = [self.__convert_to_bytes(expect)]
        return self._tn.expect(new_except_list, timer)

    def run(self, command):
        self._tn.write(self.__convert_to_bytes(command) + self.eol)

    def run_and_expect(self, command: str, expect, timer=30):
        """Return (0/-1, None/match_object, text till up match_object)"""
        self.run(command)
        return self.expect(expect, timer)

    def read_all(self):
        """Read readily available data"""

        return self._tn.read_very_eager()

    def ctrlc(self):
        """Run ctrl+c command analog"""

        self.run(b"quit")

    @staticmethod
    def __convert_to_bytes(value):
        """ Convert to bytes any types of data"""

        result = None
        if isinstance(value, str):
            result = value.encode('utf8')
        elif isinstance(value, (float, int,)):
            result = str(value).encode('utf8')
        elif isinstance(value, bytes):
            result = value
        else:
            result = bytes(value)
        return result
