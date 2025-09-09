PHONY: test

test: 
	poetry run poe test

cpproto:
	cp -r ./orca/protobufs/python/* ./proto/

