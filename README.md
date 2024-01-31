# topssh

a package on top of fabric to use ssh easily

## installation

```bash
pip install topssh
```

## usage

```python
from topssh.ssh_lite import SSH
from topssh.ssh import SSH as FullSSH

host = "127.0.0.1"
user ="username"
password = "password"

# lite ssh only captures command output
ssh = SSH(host, user, password)
ssh.add_sudo_watcher()
ssh.connect(timeout=5)

out = ssh.run("hostname")
print(out)

out = ssh.run("uname -a")
print(out)

# all outpus in ssh.echo_text
print("".join(ssh.echo_text))

# full ssh cpatures all output including command input and output
ssh = FullSSH(host, user, password)
ssh.connect(timeout=5)

# add timestamps to output and ignore color chars
# ssh.patch_output()

out = ssh.run("hostname")
print(out)

out = ssh.run("uname -a")
print(out)

# all outpus in ssh.echo_text
print("".join(ssh.echo_text))

```
