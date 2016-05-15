#!/bin/sh
hcidump --raw -i hci0 | grep '^>.\{50\}'
