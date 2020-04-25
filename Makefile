VERSION            = 0.6.1
REPO_PATH         ?= $(shell pwd)
CHROOT_PATH       ?= $(shell pwd)/buildroot
CHROOT_DEB_MIRROR ?= http://ftp.de.debian.org/debian
CCU_PREDIST_PATH  ?= $(shell pwd)/ccu_pkg
DIST_PATH         ?= $(shell pwd)/dist
CCU_PKG_PATH      ?= $(DIST_PATH)/ccu
CCU_HOST          ?= ccu3-webui

# On OS X with macports coverage has no "coverage" link
COVERAGE2 := $(shell if which coverage2 >/dev/null 2>&1; then echo coverage2; \
		   elif which coverage-2.7 >/dev/null 2>&1; then echo coverage-2.7; \
		   elif which coverage >/dev/null 2>&1; then echo coverage; fi)

COVERAGE3 := $(shell if which coverage3 >/dev/null 2>&1; then echo coverage3; \
		   elif which coverage-3.4 >/dev/null 2>&1; then echo coverage-3.4; fi)

.PHONY: dist


help:
	@echo
	@echo "Available commands:"
	@echo
	@echo "setup              - Install packages needed for development (at least on debian)"
	@echo "version            - Set a new version number"
	@echo
	@echo "dist		  - Create all release packages"
	@echo "dist-os            - Create release package for regular systems (Only pmatic)"
	@echo "dist-ccu-step1     - Copies needed python files to dist/ccu directory, the chroot"
	@echo "                     needs to be created with \"make chroot\" before. The files below"
	@echo "                     dist/ccu will be added to git to make CCU packaging without "
	@echo "                     a chroot environment possible (like needed for travis containers)"
	@echo "dist-ccu-step2     - Create addon package for installation on CCU (Python + pmatic)"
	@echo "release            - Pack and upload pmatic to Pypi for creating a new release"
	@echo
	@echo "test	          - Run tests incl. coverage analyzing"
	@echo "coverage	          - Report test coverage (short, console)"
	@echo "coverage-html      - Report test coverage (detailed, html)"
	@echo "test-python3       - Run tests using Python3 (excl. coverage analyzing)"
	@echo "coverage	          - Report test coverage (short, console)"
	@echo "test-with-ccu      - Run remote API tests against a real CCU and record the responses"
	@echo "                     which are stored below tests/resources/ and then used as expected"
	@echo "	                    responses during regular tests."
	@echo
	@echo "install		  - Install on local system"
	@echo "install-ccu        - Install python and pmatic on the CCU via SSH"
	@echo "install-ccu-python - Install python files from chroot on CCU via SSH"
	@echo "install-ccu-pmatic - Install pmatic files on CCU via SSH"
	@echo
	@echo
	@echo "run	          - run pmatic directly from command line"
	@echo
	@echo "clean	          - Cleanup development files (e.g. chroot)"
	@echo

setup:
	sudo apt-get install debootstrap qemu-user-static rsync dialog python-pytest python-pip \
			python3-pip python-sphinx snakefood python-lxml \
			python-six 
	sudo pip install --upgrade pytest_flakes pytest_runner coverage beautifulsoup4 \
			 Pygments==2.5.2 requests cryptography html5lib
	sudo pip3 install --upgrade pytest_flakes pytest_runner coverage beautifulsoup4 \
			 sphinxcontrib-images requests cryptography html5lib
	# port install py-coverage py34-coverage \
	# 	       py-setuptools py34-setuptools \
	# 	       py-pytest py34-pytest

release: dist
	git tag v$(VERSION)
	twine register dist/pmatic-$(VERSION).tar.gz
	twine upload dist/pmatic-$(VERSION).tar.gz
	$(MAKE) version
	@echo "You now have to upload the dist/pmatic-$(VERSION)_ccu.tar.gz to GitHub manually."

dist: dist-os dist-ccu

dist-os:
	[ ! -d $(DIST_PATH) ] && mkdir $(DIST_PATH) || true
	python3 setup.py sdist
	@echo "Created dist/pmatic-$(VERSION).tar.gz"

dist-ccu:
	sudo $(MAKE) dist-ccu-step1a
	sudo $(MAKE) dist-ccu-step1b
	$(MAKE) dist-ccu-step2a
	$(MAKE) dist-ccu-step2b

dist-ccu-step1: dist-ccu-step1a dist-ccu-step1b

dist-ccu-step1a:
	mkdir -p $(CCU_PREDIST_PATH)/python
	cd $(CHROOT_PATH)/usr ; \
	rsync -aRvL --no-g $$(cat $(REPO_PATH)/ccu_pkg/python-modules.list) \
	    $(CCU_PREDIST_PATH)/python ; \
	rsync -aRL --no-g $$(cat $(REPO_PATH)/ccu_pkg/python-modules-optional.list) \
	    $(CCU_PREDIST_PATH)/python 2>/dev/null || true
	rsync -av --no-g $(CHROOT_PATH)/lib/arm-linux-gnueabi/libexpat.so.1 \
	    $(CCU_PREDIST_PATH)/python/lib/
	# Cleanup site-packages to dist-packages
	rsync -av $(CCU_PREDIST_PATH)/python/lib/python2.7/site-packages/* \
	    $(CCU_PREDIST_PATH)/python/lib/python2.7/dist-packages/
	rm -rf $(CCU_PREDIST_PATH)/python/lib/python2.7/site-packages

dist-ccu-step1b:
	mkdir -p $(CCU_PREDIST_PATH)_py3/python
	cd $(CHROOT_PATH)/usr ; \
	rsync -aRvL --no-g $$(cat $(CCU_PREDIST_PATH)_py3/python-modules.list) \
	    $(CCU_PREDIST_PATH)_py3/python ; \
	rsync -aRL --no-g $$(cat $(CCU_PREDIST_PATH)_py3/python-modules-optional.list) \
	    $(CCU_PREDIST_PATH)_py3/python 2>/dev/null || true 
	rsync -av --no-g $(CHROOT_PATH)/lib/arm-linux-gnueabi/libexpat.so.1 \
	    $(CCU_PREDIST_PATH)_py3/python/lib/
	# Cleanup site-packages to dist-packages
	rsync -av $(CCU_PREDIST_PATH)_py3/python/lib/python3.8/site-packages/* \
	    $(CCU_PREDIST_PATH)_py3/python/lib/python3.8/dist-packages/
	rm -rf $(CCU_PREDIST_PATH)_py3/python/lib/python3.8/site-packages

dist-ccu-step2: dist-ccu-step2a dist-ccu-step2b

dist-ccu-step2a:
	[ ! -d $(DIST_PATH) ] && mkdir $(DIST_PATH) || true
	[ ! -d $(CCU_PKG_PATH) ] && mkdir $(CCU_PKG_PATH) || true
	[ ! -d $(CCU_PKG_PATH)/python ] && mkdir $(CCU_PKG_PATH)/python || true
	[ ! -d $(CCU_PKG_PATH)/python/bin ] && mkdir $(CCU_PKG_PATH)/python/bin || true
	[ ! -d $(CCU_PKG_PATH)/python/lib ] && mkdir $(CCU_PKG_PATH)/python/lib || true
	rsync -av $(CCU_PREDIST_PATH)/python/bin $(CCU_PREDIST_PATH)/python/lib $(CCU_PKG_PATH)/python
	rsync -aRv --no-g \
	    --exclude=\*.pyc \
	    --exclude=.\*.swp \
	    --exclude=__pycache__ \
	    pmatic examples pmatic-manager manager_static www \
	    $(CCU_PKG_PATH)
	cd $(CCU_PKG_PATH)/python/lib/python2.7 ; python -m compileall .
	tar -cv -C $(CCU_PKG_PATH) -f $(DIST_PATH)/pmatic-$(VERSION)_ccu_2.7.tar .
	[ -d $(CCU_PKG_PATH) ] && rm -rf $(CCU_PKG_PATH) || true
	tar -rv -C ccu_pkg -f $(DIST_PATH)/pmatic-$(VERSION)_ccu_2.7.tar \
	    update_script \
	    python-wrapper \
	    pmatic.init
	tar -rv -f $(DIST_PATH)/pmatic-$(VERSION)_ccu_2.7.tar \
	    LICENSE \
	    README.rst
	tar -rv -C pmatic.egg-info -f $(DIST_PATH)/pmatic-$(VERSION)_ccu_2.7.tar \
	    PKG-INFO
	gzip -f $(DIST_PATH)/pmatic-$(VERSION)_ccu_2.7.tar
	@echo "Created dist/pmatic-$(VERSION)_ccu.tar_2.7.gz"

dist-ccu-step2b:
	[ ! -d $(DIST_PATH) ] && mkdir $(DIST_PATH) || true
	[ ! -d $(CCU_PKG_PATH) ] && mkdir $(CCU_PKG_PATH) || true
	[ ! -d $(CCU_PKG_PATH)/python ] && mkdir $(CCU_PKG_PATH)/python || true
	[ ! -d $(CCU_PKG_PATH)/python/bin ] && mkdir $(CCU_PKG_PATH)/python/bin || true
	[ ! -d $(CCU_PKG_PATH)/python/lib ] && mkdir $(CCU_PKG_PATH)/python/lib || true
	rsync -av $(CCU_PREDIST_PATH)_py3/python/bin $(CCU_PREDIST_PATH)_py3/python/lib $(CCU_PKG_PATH)/python
	rsync -aRv --no-g \
	    --exclude=\*.pyc \
	    --exclude=.\*.swp \
	    --exclude=__pycache__ \
	    pmatic examples pmatic-manager manager_static www \
	    $(CCU_PKG_PATH)
	cd $(CCU_PKG_PATH)/python/lib/python3.8 ; python3 -m compileall .
	tar -cv -C $(CCU_PKG_PATH) -f $(DIST_PATH)/pmatic-$(VERSION)_ccu_3.8.tar .
	[ -d $(CCU_PKG_PATH) ] && rm -rf $(CCU_PKG_PATH) || true
	tar -rv -C ccu_pkg_py3 -f $(DIST_PATH)/pmatic-$(VERSION)_ccu_3.8.tar \
	    update_script \
	    python-wrapper \
	    pmatic.init
	tar -rv -f $(DIST_PATH)/pmatic-$(VERSION)_ccu_3.8.tar \
	    LICENSE \
	    README.rst
	tar -rv -C pmatic.egg-info -f $(DIST_PATH)/pmatic-$(VERSION)_ccu_3.8.tar \
	    PKG-INFO
	gzip -f $(DIST_PATH)/pmatic-$(VERSION)_ccu_3.8.tar
	@echo "Created dist/pmatic-$(VERSION)_ccu.tar_3.8.gz"

test:
	@if [ -z "$(COVERAGE2)" ]; then \
	    echo "Python 2 coverage is missing" ; \
	    exit 1 ; \
	fi
	$(COVERAGE2) run --include='pmatic/*' --source=pmatic setup.py test
	@if [ -z "$(COVERAGE3)" ]; then \
	    echo "Python 3 coverage is missing" ; \
	    exit 1 ; \
	fi
	$(COVERAGE3) run -a --include='pmatic/*' --source=pmatic setup.py test
	$(MAKE) coverage coverage-html

test-python3:
	python3 setup.py test

test-with-ccu:
	TEST_WITH_CCU=1 $(MAKE) test

test-with-ccu-py3:
	TEST_WITH_CCU=1 $(COVERAGE3) run -a --include='pmatic/*' --source=pmatic setup.py test
	TEST_WITH_CCU=1 $(MAKE) coverage coverage-html

coverage:
	$(COVERAGE2) report

coverage-html:
	$(COVERAGE2) html

install:
	sudo python setup.py install
	if type python3 >/dev/null 2>&1 ; then \
	    sudo python3 setup.py install ; \
	fi

install-ccu: install-ccu-python install-ccu-pmatic install-ccu-scripts

install-ccu-python:
	ssh root@$(CCU_HOST) "[ -d /usr/local/etc/config/addons/pmatic ] || mkdir /usr/local/etc/config/addons/pmatic"
	ssh root@$(CCU_HOST) "[ -d /usr/local/etc/config/addons/pmatic/python ] || mkdir /usr/local/etc/config/addons/pmatic/python"
	rsync -av --no-g \
	    --exclude=\*.pyc \
	    --exclude=.\*.swp \
	    --exclude=__pycache__ \
	    $(CCU_PREDIST_PATH)/python/* \
	    root@$(CCU_HOST):/usr/local/etc/config/addons/pmatic/python/
	rsync -av --no-g \
	    --exclude=\*.pyc \
	    --exclude=.\*.swp \
	    --exclude=__pycache__ \
	    $(CCU_PREDIST_PATH)_py3/python/* \
	    root@$(CCU_HOST):/usr/local/etc/config/addons/pmatic/python/

install-ccu-pmatic:
	ssh root@$(CCU_HOST) "[ -d /usr/local/etc/config/addons/pmatic/etc ] || mkdir /usr/local/etc/config/addons/pmatic/etc"
	rsync -aRv --no-g \
	    --exclude=\*.pyc \
	    --exclude=.\*.swp \
	    --exclude=__pycache__ \
	    pmatic \
	    root@$(CCU_HOST):/usr/local/etc/config/addons/pmatic/python/lib/python2.7/
	rsync -aRv --no-g \
	    --exclude=\*.pyc \
	    --exclude=.\*.swp \
	    --exclude=__pycache__ \
	    pmatic \
	    root@$(CCU_HOST):/usr/local/etc/config/addons/pmatic/python/lib/python3.8/
	rsync -aRv --no-g \
	    --exclude=\*.pyc \
	    --exclude=.\*.swp \
	    --exclude=__pycache__ \
	    examples \
	    root@$(CCU_HOST):/usr/local/etc/config/addons/pmatic/scripts/
	rsync -aRv --no-g \
	    --exclude=\*.pyc \
	    --exclude=.\*.swp \
	    --exclude=__pycache__ \
	    manager_static \
	    root@$(CCU_HOST):/usr/local/etc/config/addons/pmatic
	rsync -aRv --no-g \
	    pmatic-manager \
	    root@$(CCU_HOST):/usr/local/bin/pmatic-manager
	ssh root@$(CCU_HOST) "[ -d /usr/local/etc/config/addons/www/pmatic ] || mkdir /usr/local/etc/config/addons/www/pmatic"
	rsync -av --no-g \
	    --exclude=\*.pyc \
	    --exclude=.\*.swp \
	    --exclude=__pycache__ \
	    www/update-check.cgi \
	    root@$(CCU_HOST):/usr/local/etc/config/addons/www/pmatic/update-check.cgi

install-ccu-scripts:
	rsync -av --no-g \
	    ccu_pkg_py3/pmatic.init \
	    root@$(CCU_HOST):/usr/local/etc/config/rc.d/pmatic

version:
	@newversion=$$(dialog --stdout --inputbox "New Version:" 0 0 "$(VERSION)") ; \
        if [ -n "$$newversion" ] ; then \
            $(MAKE) NEW_VERSION=$$newversion setversion ; \
        fi

setversion:
	sed -ri 's/^(VERSION[[:space:]]*= *).*/\1'"$(NEW_VERSION)/" Makefile
	sed -ri "s/^(__version__[[:space:]]*= *).*/\1\"$(NEW_VERSION)\"/g" pmatic/__init__.py
	sed -i "s/version='.*',/version='$(NEW_VERSION)',/g" setup.py
	sed -i "s/^VERSION=.*/VERSION=$(NEW_VERSION)/g" ccu_pkg/pmatic.init

clean: clean-dist clean-test
	$(MAKE) -C doc clean

clean-test:
	rm -rf tests/__pycache__ || true
	sudo rm -rf pmatic.egg-info || true
	rm -rf *.egg || true
	rm -rf .coverage htmlcov || true
	rm -rf .cache || true

clean-dist:
	sudo rm -rf build 2>/dev/null || true
	sudo rm -rf dist 2>/dev/null || true
	sudo rm -rf $(CCU_PKG_PATH)/python 2>/dev/null || true
	sudo rm -rf $(CCU_PKG_PATH)/python3 2>/dev/null || true
	sudo rm -rf $(CCU_PREDIST_PATH)/python 2>/dev/null || true
	sudo rm -rf $(CCU_PREDIST_PATH)_py3/python 2>/dev/null || true


travis-build:
	GIT_COMMIT=$(shell git rev-parse --short HEAD) ; \
	NEW_VERSION=$$GIT_COMMIT $(MAKE) setversion ; \
	$(MAKE) dist-os dist-ccu-step2a ; \
	$(MAKE) dist-os dist-ccu-step2b ; \
	PKG_PATH=$(shell pwd)/dist ; \
	cd $$HOME ; \
	git config --global user.email "travis@travis-ci.org" ; \
	git config --global user.name "Travis" ; \
	git clone --quiet --branch=gh-pages https://$$GH_TOKEN@github.com/mweiss/pmatic.git gh-pages > /dev/null ; \
	cd gh-pages ; \
	cp -f $$PKG_PATH/pmatic-$${GIT_COMMIT}_ccu.tar.gz pmatic-snapshot_ccu.tar.gz ; \
	cp -f $$PKG_PATH/pmatic-$${GIT_COMMIT}.tar.gz pmatic-snapshot.tar.gz ; \
	git add -f . ; \
	git commit -m "Travis build $$TRAVIS_BUILD_NUMBER pushed to gh-pages" ; \
	git push -fq origin gh-pages > /dev/null ; \
	echo "Finished adding current build"

# Assumes travis-build was executed before
travis-doc:
	PKG_PATH=$(shell pwd)/doc ; \
	cd doc ; \
	$(MAKE) html ; \
	cd $$HOME/gh-pages ; \
	cp -rf $$PKG_PATH/_build/html/* doc/ ; \
	git add -f doc/* ; \
	git commit -m "Travis doc $$TRAVIS_BUILD_NUMBER pushed to gh-pages" ; \
	git push -fq origin gh-pages > /dev/null ; \
	echo "Finished adding current docs"

run:
	[ ! -d etc ] && mkdir etc || true; \
	python pmatic-manager -g -o etc -e . -r examples -t ./manager_static -f etc/pmatic.log
