
.PHONY: setup run clean list-envs activate help

ENV_NAME=translator

setup:
	@echo "🔧 Creating environment..."
	@bash setup.sh

list-envs:
	@conda env list

activate:
	@echo "👉 Run manually:"
	@echo "conda activate $(ENV_NAME)"

clean:
	@echo "🧹 Removing environment..."
	@conda remove --name $(ENV_NAME) --all -y

run:
	"🚀 Running application with conda environment '$(ENV_NAME)'..."
	@source "$(shell conda info --base)/etc/profile.d/conda.sh" && 
			 conda activate $(ENV_NAME) && 
			 python $(PYTHON_FILE)