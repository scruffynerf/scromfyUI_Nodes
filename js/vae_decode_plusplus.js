// vae_decode_plusplus.js
// Originally part of VAE-Decode-PlusPlus (GPL v3)
//
// This file controls the UI for the VAE Decode PlusPlus node.
// It uses a new strategy to truly remove widgets from the layout.

import { app } from "/scripts/app.js";

app.registerExtension({
    name: "VAE-Decode-PlusPlus.UI.NewStrategy", // A new name for a new approach.
    async beforeRegisterNodeDef(nodeType, nodeData) {
        // Check if this is the node we want to modify.
        if (nodeData.name === "VAEDecodePlusPlus") {
            console.log("[VAE-Decode-PlusPlus] Applying new layout strategy to VAEDecodePlusPlus.");

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                onNodeCreated?.apply(this, arguments);

                // Find all the widgets we need to control.
                const decoderWidget = this.widgets.find((w) => w.name === "select_decoder");
                const tiledWidgets = [
                    "tile_size",
                    "overlap",
                    "temporal_size",
                    "temporal_overlap",
                ].map(name => this.widgets.find(w => w.name === name));

                // Store the original properties of the widgets so we can restore them.
                for (const widget of tiledWidgets) {
                    if (widget) {
                        // We only need to store the original computeSize.
                        widget._original_computeSize = widget.computeSize;
                    }
                }

                const toggleVisibility = (isTiled) => {
                    for (const widget of tiledWidgets) {
                        if (!widget) continue;

                        // Set the widget's hidden property. This prevents it from being drawn,
                        // which should fix the background flicker issue.
                        widget.hidden = !isTiled;

                        if (isTiled) {
                            // If we want to show the widget, restore its original size calculation.
                            widget.computeSize = widget._original_computeSize;
                        } else {
                            // If we want to hide it, replace its size calculation with one
                            // that removes it from the layout, fixing the gap.
                            widget.computeSize = function () { return [0, -4]; } // -4 accounts for margin
                        }
                    }

                    // Force the node to immediately re-evaluate its size and redraw.
                    // This is the key to preventing the gap when switching back to default.
                    this.size = this.computeSize();
                    this.setDirtyCanvas(true, true);
                };

                // When the dropdown changes, run our new visibility logic.
                decoderWidget.callback = (value) => {
                    toggleVisibility(value === "tiled");
                };

                // Run once on creation to set the correct initial state.
                setTimeout(() => {
                    decoderWidget.callback(decoderWidget.value);
                }, 10);
            };
        }
    },
});
