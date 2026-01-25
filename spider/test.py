from urllib.robotparser import RobotFileParser

a = {}
rp = RobotFileParser()
rp.parse([])
a['example.com'] = rp
print(a['example.com'].can_fetch('*','/somepath'))  # True