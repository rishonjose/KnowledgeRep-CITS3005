#!/bin/bash
# Script to repopulate the knowledge graph

echo "Repopulating the knowledge graph..."
/opt/homebrew/Caskroom/miniconda/base/envs/knowrep/bin/python ontology/populate.py

if [ $? -eq 0 ]; then
    echo "✅ Knowledge graph repopulated successfully!"
    echo "You can now restart the Flask application."
else
    echo "❌ Error repopulating knowledge graph"
    exit 1
fi
