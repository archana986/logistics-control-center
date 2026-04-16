# Databricks notebook source
# MAGIC %md
# MAGIC # Install Logistics Demo Skill for Genie Code
# MAGIC
# MAGIC Run this notebook once to install the deployment skill into your
# MAGIC Genie Code user skills folder. After installation, Genie Code will
# MAGIC auto-load the skill when you ask about deploying or setting up the
# MAGIC logistics demo, or you can invoke it with `@logistics-demo`.

# COMMAND ----------

import os
import shutil

# Detect current user
username = spark.sql("SELECT current_user()").collect()[0][0]

# Source: skill files in this repo's harness/ directory
repo_path = os.path.dirname(os.path.abspath(__file__))
harness_path = os.path.join(repo_path)
skill_source = harness_path

# Destination: user's .assistant/skills/ directory
skill_dest = f"/Workspace/Users/{username}/.assistant/skills/logistics-demo"

print(f"Source:      {skill_source}")
print(f"Destination: {skill_dest}")

# COMMAND ----------

# Copy SKILL.md and resources/ to the user skills folder
os.makedirs(skill_dest, exist_ok=True)

# Copy SKILL.md
shutil.copy2(
    os.path.join(skill_source, "SKILL.md"),
    os.path.join(skill_dest, "SKILL.md")
)
print("Copied SKILL.md")

# Copy resources/
resources_src = os.path.join(skill_source, "resources")
resources_dest = os.path.join(skill_dest, "resources")
if os.path.exists(resources_dest):
    shutil.rmtree(resources_dest)
shutil.copytree(resources_src, resources_dest)
print("Copied resources/")

# COMMAND ----------

# Verify installation
for root, dirs, files in os.walk(skill_dest):
    for f in files:
        path = os.path.join(root, f)
        print(f"  Installed: {path}")

print(f"\nSkill installed. In Genie Code Agent mode, type '@logistics-demo' or ask about deploying the logistics demo.")
