# Makefile — logis
# Deploy por symlink para o perfil default do QGIS.

PLUGINNAME = logis
VERSION = $(shell grep '^version=' $(PLUGINNAME)/metadata.txt | cut -d= -f2)
# QGIS_MAJOR escolhe o perfil de destino: 3 (Qt5) ou 4 (Qt6).
# metadata.txt aceita 3.16-4.99; use `make deploy-qgis4` para o perfil QGIS4.
QGIS_MAJOR ?= 3
QGIS_PLUGINS = $(HOME)/.local/share/QGIS/QGIS$(QGIS_MAJOR)/profiles/default/python/plugins
FLATPAK_PLUGINS = $(HOME)/.var/app/org.qgis.qgis/data/QGIS/QGIS$(QGIS_MAJOR)/profiles/default/python/plugins
TARGET = $(QGIS_PLUGINS)/$(PLUGINNAME)
FLATPAK_TARGET = $(FLATPAK_PLUGINS)/$(PLUGINNAME)
SRC = $(CURDIR)/$(PLUGINNAME)

.PHONY: deploy deploy-flatpak deploy-qgis4 deploy-flatpak-qgis4 undeploy undeploy-flatpak clean test package i18n transcompile help

help:
	@echo "make deploy          - symlink do plugin no perfil QGIS3 do sistema"
	@echo "make deploy-flatpak  - symlink no perfil QGIS3 do QGIS Flatpak"
	@echo "make deploy-qgis4    - idem deploy, mas no perfil QGIS4 (Qt6)"
	@echo "make deploy-flatpak-qgis4 - idem deploy-flatpak, mas no perfil QGIS4 (Qt6)"
	@echo "make undeploy        - remove o symlink (sistema)"
	@echo "make undeploy-flatpak- remove o symlink (flatpak)"
	@echo "make clean           - remove __pycache__"
	@echo "make test            - smoke test de sintaxe (sem QGIS)"
	@echo "make package         - gera o pacote zip via qgis-plugin-ci em dist/logis-<version>.zip"
	@echo "make i18n            - extrai strings self.tr(...) para i18n/logis_pt_BR.ts"
	@echo "make transcompile    - compila i18n/*.ts para .qm (lrelease)"

deploy:
	@mkdir -p $(QGIS_PLUGINS)
	@if [ -e "$(TARGET)" ] && [ ! -L "$(TARGET)" ]; then \
		echo "ERRO: $(TARGET) existe e nao e symlink. Remova manualmente."; exit 1; \
	fi
	@ln -sfn "$(SRC)" "$(TARGET)"
	@echo "symlink: $(TARGET) -> $(SRC)"
	@echo "Recarregue no QGIS (Plugin Reloader) ou reinicie."

deploy-flatpak:
	@if [ ! -d "$(dir $(FLATPAK_PLUGINS))" ]; then \
		echo "ERRO: perfil Flatpak nao existe ainda."; exit 1; \
	fi
	@mkdir -p "$(FLATPAK_PLUGINS)"
	@if [ -e "$(FLATPAK_TARGET)" ] && [ ! -L "$(FLATPAK_TARGET)" ]; then \
		echo "ERRO: $(FLATPAK_TARGET) existe e nao e symlink."; exit 1; \
	fi
	@ln -sfn "$(SRC)" "$(FLATPAK_TARGET)"
	@echo "symlink (flatpak): $(FLATPAK_TARGET) -> $(SRC)"

deploy-qgis4:
	@$(MAKE) QGIS_MAJOR=4 deploy

deploy-flatpak-qgis4:
	@$(MAKE) QGIS_MAJOR=4 deploy-flatpak

undeploy:
	@if [ -L "$(TARGET)" ]; then rm "$(TARGET)" && echo "removido $(TARGET)"; \
	else echo "nada a remover"; fi

undeploy-flatpak:
	@if [ -L "$(FLATPAK_TARGET)" ]; then rm "$(FLATPAK_TARGET)" && echo "removido $(FLATPAK_TARGET)"; \
	else echo "nada a remover"; fi

clean:
	@find . -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "limpo"

test:
	@python3 -c "import ast,glob,sys; [ast.parse(open(f).read(), f) for f in glob.glob('**/*.py', recursive=True)]; print('sintaxe OK')"

package:
	@mkdir -p dist
	@qgis-plugin-ci package $(VERSION) --disable-submodule-update
	@mv $(PLUGINNAME).$(VERSION).zip dist/$(PLUGINNAME)-$(VERSION).zip 2>/dev/null || true
	@echo "Pacote gerado em dist/$(PLUGINNAME)-$(VERSION).zip"

i18n:
	@mkdir -p i18n
	@pylupdate5 $(PLUGINNAME)/provider.py $(PLUGINNAME)/logis_plugin.py $(PLUGINNAME)/gui/*.py $(PLUGINNAME)/algorithms/*.py -ts $(PLUGINNAME)/i18n/logis_pt_BR.ts $(PLUGINNAME)/i18n/logis_en.ts

transcompile:
	@lrelease $(PLUGINNAME)/i18n/*.ts

