import ConfigParser

class _FruitConfigParser(ConfigParser.SafeConfigParser):
    def get_all(self, section, option):
        results = []
        index = 1

        try:
            while True:
                results.append(self.get(section, "%s.%d" % (option, index)))
                index += 1

        except ConfigParser.NoOptionError:
            return results

config = _FruitConfigParser()
