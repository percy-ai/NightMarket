from flask import Flask, request, jsonify, send_from_directory
from database.hok_db import Hok_DB
from managers.dialogue_manager import Dialogue_Manager
from managers.vendor_manager import Vendor_Manager
from managers.challenge_manager import Challenge_Manager
import base64
import os
import re

class App:
    def __init__(self, mode=2):
        self.mode = mode
        self.dialogue_manager = None
        self.vendor_manager = None
        self.challenge_manager = None
        self.app = None

    def run(self, host="0.0.0.0", port=8000, debug=False):
        self.create_app()
        self.create_endpoints()
        self.app.run(host=host, port=port, debug=debug)

    def create_app(self):
        self.dialogue_manager = Dialogue_Manager(self.mode)
        self.vendor_manager = Vendor_Manager(self.mode)
        self.challenge_manager = Challenge_Manager(self.mode)
            
        self.app = Flask(import_name="Hokkien Game")

        @self.app.after_request
        def add_cors_headers(response):
            # Allow browser-based clients (e.g., Unity WebGL) to call this API cross-origin.
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            return response

    def create_endpoints(self):
        print("\nStarting Flask app...")
        #mock data for contract apis
        MOCK_USER_STATS = {
            "u123": {
                "user_id": "u123",
                "current_streak": 5,
                "last_active_date": "2026-02-20",
                "activity_heatmap": {
                    "2026-02-18": 5,
                    "2026-02-19": 12,
                    "2026-02-20": 8
                },
                "preferred_language": "hokkien"
            }
        }

        MOCK_USER_INVENTORY = {
            "u123": {
                "user_id": "u123",
                "active_challenge_id": "c001",
                "inventory": [
                    {
                        "item_id": "item_apple",
                        "challenge_id": "c001",
                        "acquired_at": "2026-03-19T20:00:00Z"
                    },
                    {
                        "item_id": "item_peanut",
                        "challenge_id": "c001",
                        "acquired_at": "2026-03-19T20:05:00Z"
                    }
                ]
            },
            "u_4eaab2a1": {
                "user_id": "u_4eaab2a1",
                "active_challenge_id": "c_mock_01",
                "inventory": [
                    {
                        "item_id": "item_noodle",
                        "challenge_id": "c_mock_01",
                        "acquired_at": "2026-03-19T20:10:00Z"
                    },
                    {
                        "item_id": "item_soup",
                        "challenge_id": "c_mock_01",
                        "acquired_at": "2026-03-19T20:11:00Z"
                    }
                ]
            }
        }

        DEFAULT_MOCK_INVENTORY = {
            "active_challenge_id": "c_mock_01",
            "inventory": [
                {
                    "item_id": "item_noodle",
                    "challenge_id": "c_mock_01",
                    "acquired_at": "2026-03-19T20:10:00Z"
                },
                {
                    "item_id": "item_soup",
                    "challenge_id": "c_mock_01",
                    "acquired_at": "2026-03-19T20:11:00Z"
                }
            ]
        }

        @self.app.route("/api/v1/user/<user_id>/stats", methods=["GET"])
        def api_get_user_stats(user_id):
            user = MOCK_USER_STATS.get(user_id)
            if not user:
                # simple default if unknown user
                user = {
                    "user_id": user_id,
                    "current_streak": 0,
                    "last_active_date": None,
                    "activity_heatmap": {},
                    "preferred_language": "hokkien"
                }
            return jsonify(user), 200

        @self.app.route("/api/v1/vendors/<vendor_id>", methods=["GET"])
        def get_vendor_profile(vendor_id):
            """Gets the dialogue node given the node id
        
            Args:
                node_id: Id of dialogue node
                
            Returns:
                {
                    "status": "success",
                    "data": {
                        "vendor_id": "vendor_id",
                        "dialogue_node_id": "dialogue_node_id",
                        "vendor_name": "vendor_name",
                        "items": [items],
                    },
                    "meta": {"processTimeMS": 123}
                }
            """
            vendor_data = self.vendor_manager.get_vendor_profile(vendor_id)

            return jsonify({
                "status": "success",
                "data": vendor_data,
                "meta": {"processTimeMS": 123}
            }), 200

        @self.app.route("/api/v1/dialogue/<node_id>", methods=["GET"])
        def get_dialogue_node(node_id):
            """Gets the dialogue node given the node id
        
            Args:
                node_id: Id of dialogue node
                
            Returns:
                {
                    "status": "success",
                    "data": {
                        "dialogue_node": "node_id",
                        "dialogue": {
                            "dialogue_id": "id of dialogue",
                            "text": "text of the dialogue",
                            "translation": "translation of the text",
                            "audio": "audio of the text",
                            "npc_id": "id of npc dialogue belongs to",
                            "key_words": [{
                                "word_id": "id of word",
                                "word": "word",
                                "translation": "translation of word",
                                "context": "context of word",
                                "audio": "audio of word"
                            }]
                        },
                        "options": [{
                            "option_id": "id of options",
                            "text": "text of the option",
                            "next_node": "node to the next dialogue node",
                            "feedback_type": "feedback type of option",
                            "event": "event"
                        }],
                        "next_nodes": [
                            "array of next nodes",
                            "Note: should only be used if the dialogue is not branching"
                        ]
                    }
                    "meta": {"processTimeMS": 123}
                }
            """
            node_data = self.dialogue_manager.get_dialogue_node(node_id)
            
            return jsonify({
                "status": "success",
                "data": node_data,
                "meta": {"processTimeMS": 123}
            }), 200
        
        @self.app.route("/api/v1/dialogue/root-nodes/<npc_id>")
        def get_dialogue_root_nodes(npc_id):
            """Gets all the root dialogue nodes that are related to given npc 
        
            Args:
                npc_id: Id of npc
                
            Returns:
                {
                    "status": "success",
                    "data": {
                        "npc_id": "npc_id",
                        "root_node_ids": ["ids of root node"]
                    },
                    "meta": {"processTimeMS": 123}
                }
            """
            node_data = self.dialogue_manager.get_dialogue_root_nodes(npc_id)
            
            return jsonify({
                "status": "success",
                "data": node_data,
                "meta": {"processTimeMS": 123}
            }), 200

        @self.app.route("/api/v1/generate/sentences", methods=["POST"])
        def fetch_sentences():
            request_body = request.get_json()
            input_text = request_body.get("input_text")

            if self.mode == "test_mode":
                english_text = chinese_text = hokkien_text = "this output is a test output"
            else:
                english_text = chinese_text = hokkien_text = "calls model api for translation"
            
            return jsonify({
                "status": "success",
                "data": {
                    "input_text": input_text,
                    "english_text": english_text,
                    "chinese_text": chinese_text,
                    "hokkien_text": hokkien_text
                },
                "meta": {"processTimeMS": 123}
            }), 200

        @self.app.route("/api/v1/generate/translation", methods=["POST"])
        def fetch_translation():
            request_body = request.get_json()
            source_lang = request_body.get("source_lang")
            output_lang = request_body.get("output_lang")
            model_parameters = request_body.get("parameters")
            input_text = request_body.get("input_text")

            model_out = "this output is a test output" if self.mode == "test_mode" else "calls model api for translation"
            
            return jsonify({
                "status": "success",
                "data": {
                    "source_lang": source_lang,
                    "output_lang": output_lang,
                    "parameters": model_parameters,
                    "input_text": input_text,
                    "translated_text": model_out
                },
                "meta": {"processTimeMS": 123}
            }), 200
        
        @self.app.route("/api/v1/generate/romanizer", methods=["POST"])
        def fetch_romanizer():
            request_body = request.get_json()
            source_lang = request_body.get("source_lang")
            output_lang = request_body.get("output_lang")
            input_text = request_body.get("input_text")

            romanized_text = "this output is a test output" if self.mode == "test_mode" else "calls model api for romanization"

            return jsonify({
                "status": "success",
                "data": {
                    "source_lang": source_lang,
                    "output_lang": output_lang,
                    "input_text": input_text,
                    "romanized_text": romanized_text
                },
                "meta": {"processTimeMS": 123}
            }), 200

        # might not be used
        @self.app.route("/api/v1/generate/image", methods=["POST"])
        def generate_image():
            request_body = request.get_json()
            input_text = request_body.get("input_text")
            negative_prompt = request_body.get("negative_prompt")
            negative_prompt_style = request_body.get("negative_prompt_style")
            n_steps = request_body.get("n_steps")
            high_noise_frac = request_body.get("high_noise_frac")
            base64_string = request_body.get("base64_string")
            
            generate_image = "this output is a test output" if self.mode == "test_mode" else "calls model api for image generation"

            return jsonify({
                "status": "success",
                "data": {
                    "input_text": input_text,
                    "negative_prompt": negative_prompt,
                    "negative_prompt_style": negative_prompt_style,
                    "n_steps": n_steps,
                    "high_noise_frac": high_noise_frac,
                    "base64_string": base64_string,
                    "generate_image": generate_image
                },
                "meta": {"process_time_ms": 123}
            }), 200

        @self.app.route("/api/v1/generate/numeric-tones", methods=["POST"])
        def fetch_numeric_tones():
            request_body = request.get_json()
            input_text = request_body.get("input_text")
            source_lang = request_body.get("source_lang")
            output_lang = request_body.get("output_lang")

            numeric_tones = "this output is a test output" if self.mode == "test_mode" else "calls model api for numeric tones"

            return jsonify({
                "status": "success",
                "data": {
                    "source_lang": source_lang,
                    "output_lang": output_lang,
                    "input_text": input_text,
                    "numeric_tones": numeric_tones
                },
                "meta": {"process_time_ms": 123}
            }), 200
        
        @self.app.route("/api/v1/generate/audio-url", methods=["POST"])
        def fetch_audio_url():
            request_body = request.get_json()
            input_text = request_body.get("input_text")
            source_lang = request_body.get("source_lang")
            output_lang = request_body.get("output_lang")

            audio_url = "this output is a test output" if self.mode == "test_mode" else "aaaa"

            return jsonify({
                "status": "success",
                "data": {
                    "source_lang": source_lang,
                    "output_lang": output_lang,
                    "input_text": input_text,
                    "audio_url": audio_url
                },
                "meta": {"process_time_ms": 123}
            }), 200
        
        @self.app.route("/api/v1/generate/audio-blob", methods=["POST"])
        def fetch_audio_blob():
            request_body = request.get_json()
            input_text = request_body.get("input_text")
            source_lang = request_body.get("source_lang")
            output_lang = request_body.get("output_lang")

            audio_blob = "this output is a test output" if self.mode == "test_mode" else "aaaa"

            return jsonify({
                "status": "success",
                "data": {
                    "source_lang": source_lang,
                    "output_lang": output_lang,
                    "input_text": input_text,
                    "audio_blob": audio_blob
                },
                "meta": {"process_time_ms": 123}
            }), 200
        
        @self.app.route("/cat-fact")
        def get_cat_fact():
            return jsonify({
                "status": "success",
                "data": {
                    "cat_fact": "Adult cats rarely meow at each other; they developed this sound specifically to communicate with humans."
                },
                "meta": {"processTimeMS": 123}
            }), 200
        
        @self.app.route("/audio-test")
        def get_audio_test():
            with open("audio-clips/test_audio.mp3", 'rb') as f:
                encoded_string = base64.b64encode(f.read()).decode('utf-8')

            return jsonify({
                "status": "success",
                "data": {
                    "audio_clip": encoded_string
                },
                "meta": {"processTimeMS": 123}
            }), 200

        #minigame api endpoints
        @self.app.route("/api/v1/challenges", methods=["GET"])
        def get_challenges():
            """Returns lightweight list of all available challenges."""
            challenges = self.challenge_manager.get_all_challenges()
            return jsonify({
                "status": "success",
                "data": challenges,
                "meta": {"processTimeMS": 123}
            }), 200
        
        @self.app.route("/api/v1/challenges/<challenge_id>", methods=["GET"])
        def get_challenge(challenge_id):
            """Returns full details and requirements for a specific challenge."""
            challenge = self.challenge_manager.get_challenge(challenge_id)
            if not challenge:
                return jsonify({
                    "status": "error",
                    "message": "Challenge not found: %s" % challenge_id
                }), 404
            return jsonify({
                "status": "success",
                "data": challenge,
                "meta": {"processTimeMS": 123}
            }), 200
        
        @self.app.route("/api/v1/challenges/accept", methods=["POST"])
        def accept_challenge():
            """Accepts a challenge for a user. Only one active challenge at a time."""
            body = request.get_json()
            user_id = body.get("user_id")
            challenge_id = body.get("challenge_id")
 
            if not user_id or not challenge_id:
                return jsonify({
                    "status": "error",
                    "message": "user_id and challenge_id are required"
                }), 400
            
            result, error = self.challenge_manager.accept_challenge(user_id, challenge_id)
            if error:
                return jsonify({
                    "status": "error",
                    "message": error
                }), 400
 
            return jsonify({
                "status": "success",
                "data": result,
                "meta": {"processTimeMS": 123}
            }), 200
        
        @self.app.route("/api/v1/challenges/inventory", methods=["POST"])
        def add_to_inventory():
            """Adds an item to the user's inventory. Triggered by ADD_TO_INVENTORY event."""
            body = request.get_json()
            user_id = body.get("user_id")
            item_id = body.get("item_id")
            challenge_id = body.get("challenge_id")
 
            if not user_id or not item_id:
                return jsonify({
                    "status": "error",
                    "message": "user_id and item_id are required"
                }), 400
 
            result, error = self.challenge_manager.add_to_inventory(user_id, item_id, challenge_id)
            if error:
                return jsonify({
                    "status": "error",
                    "message": error
                }), 400
 
            return jsonify({
                "status": "success",
                "data": result,
                "meta": {"processTimeMS": 123}
            }), 200
        
        @self.app.route("/api/v1/user/<user_id>/inventory", methods=["GET"])
        def get_user_inventory(user_id):
            """Returns user's full inventory and active challenge. Called on login to restore session."""
            inventory = self.challenge_manager.get_user_inventory(user_id)

            # Temporary mock fallback: return hard-coded inventory when no DB data exists.
            no_db_data = (
                inventory.get("active_challenge_id") is None and
                len(inventory.get("inventory", [])) == 0
            )
            if no_db_data:
                inventory = MOCK_USER_INVENTORY.get(user_id, {
                    "user_id": user_id,
                    "active_challenge_id": DEFAULT_MOCK_INVENTORY["active_challenge_id"],
                    "inventory": DEFAULT_MOCK_INVENTORY["inventory"]
                })

            return jsonify({
                "status": "success",
                "data": inventory,
                "meta": {"processTimeMS": 123}
            }), 200
 
        @self.app.route("/api/v1/challenges/verify", methods=["POST"])
        def verify_challenge():
            """Verifies challenge completion. Run when ADD_TO_INVENTORY event fires."""
            body = request.get_json()
            user_id = body.get("user_id")
            challenge_id = body.get("challenge_id")
            final_order = body.get("final_order")
  
            if not user_id or not challenge_id or final_order is None:
                return jsonify({
                    "status": "error",
                    "message": "user_id, challenge_id and final_order are required"
                }), 400
  
            is_success, reason = self.challenge_manager.verify_challenge(
                user_id, challenge_id, final_order)
  
            return jsonify({
                "status": "success",
                "data": {
                    "is_success": is_success,
                    "challenge_id": challenge_id,
                    "reason": reason
                },
                "meta": {"processTimeMS": 123}
            }), 200

        admin_dir = os.path.join(os.path.dirname(__file__), "admin", "static")

        @self.app.route("/admin")
        def admin_index():
            return send_from_directory(admin_dir, "index.html")

        @self.app.route("/admin/<path:filename>")
        def admin_static(filename):
            return send_from_directory(admin_dir, filename)

        @self.app.route("/api/admin/npcs", methods=["GET"])
        def admin_get_npcs():
            npcs = self.dialogue_manager.get_all_npcs()
            return jsonify({
                "status": "success",
                "data": [{"npc_id": n[0], "npc_name": n[1]} for n in npcs]
            }), 200

        @self.app.route("/api/admin/npcs", methods=["POST"])
        def admin_create_npc():
            body = request.get_json()
            npc_id = body.get("npc_id")
            npc_name = body.get("npc_name")
            if not npc_id or not npc_name:
                return jsonify({"status": "error", "message": "npc_id and npc_name required"}), 400
            result = self.dialogue_manager.create_npc(npc_id, npc_name)
            return jsonify({"status": "success", "data": result}), 201

        @self.app.route("/api/admin/npcs/<npc_id>", methods=["PUT"])
        def admin_update_npc(npc_id):
            body = request.get_json()
            npc_name = body.get("npc_name")
            if not npc_name:
                return jsonify({"status": "error", "message": "npc_name required"}), 400
            result = self.dialogue_manager.update_npc(npc_id, npc_name)
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/npcs/<npc_id>", methods=["DELETE"])
        def admin_delete_npc(npc_id):
            result, success = self.dialogue_manager.delete_npc(npc_id)
            if not success:
                return jsonify({"status": "error", "message": result.get("error")}), 400
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/dialogue-nodes", methods=["GET"])
        def admin_get_nodes():
            npc_id = request.args.get("npc_id")
            if not npc_id:
                return jsonify({"status": "error", "message": "npc_id required"}), 400
            nodes = self.dialogue_manager.get_nodes_for_npc(npc_id)
            dialogues = {}
            for node in nodes:
                d = self.dialogue_manager.get_dialogue(node[0])
                if d:
                    audio_binary = ""
                    if d[0][4] != "":
                        with open(d[0][4], "rb") as f:
                            audio_binary = base64.b64encode(f.read()).decode("utf-8")
                    audio_src = { "audio_path": d[0][4], "audio_binary": audio_binary }
                    dialogues[node[0]] = {"dialogue_id": d[0][1], "dialogue": d[0][2], "translation": d[0][3], "audio_src": audio_src }
            return jsonify({
                "status": "success",
                "data": [{"node_id": n[0], "parent_node_id": n[1], "npc_id": n[2], "dialogue": dialogues.get(n[0])} for n in nodes]
            }), 200

        @self.app.route("/api/admin/dialogue-nodes", methods=["POST"])
        def admin_create_node():
            body = request.get_json()
            node_id = body.get("node_id")
            parent_node_id = body.get("parent_node_id")
            npc_id = body.get("npc_id")
            if not node_id or not parent_node_id or not npc_id:
                return jsonify({"status": "error", "message": "node_id, parent_node_id, npc_id required"}), 400
            result = self.dialogue_manager.create_node(node_id, parent_node_id, npc_id)
            dialogue_id = f"d_{node_id}"
            self.dialogue_manager.create_dialogue(node_id, dialogue_id, "", "", npc_id)
            return jsonify({"status": "success", "data": result}), 201

        @self.app.route("/api/admin/dialogue-nodes/<node_id>", methods=["PUT"])
        def admin_update_node(node_id):
            body = request.get_json()
            parent_node_id = body.get("parent_node_id")
            if not parent_node_id:
                return jsonify({"status": "error", "message": "parent_node_id required"}), 400
            result = self.dialogue_manager.update_node(node_id, parent_node_id)
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/dialogue-nodes/<node_id>", methods=["DELETE"])
        def admin_delete_node(node_id):
            result, success = self.dialogue_manager.delete_node(node_id)
            if not success:
                return jsonify({"status": "error", "message": result.get("error")}), 400
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/dialogues/<node_id>", methods=["GET"])
        def admin_get_dialogue(node_id):
            d = self.dialogue_manager.get_dialogue(node_id)
            if not d:
                return jsonify({"status": "error", "message": "Dialogue not found"}), 404
            return jsonify({
                "status": "success",
                "data": {"node_id": d[0][0], "dialogue_id": d[0][1], "dialogue": d[0][2], "translation": d[0][3], "audio_src": d[0][4], "npc_id": d[0][5]}
            }), 200

        @self.app.route("/api/admin/dialogues/<node_id>", methods=["PUT"])
        def admin_update_dialogue(node_id):
            body = request.get_json()
            dialogue_text = body.get("dialogue")
            translation = body.get("translation")
            if dialogue_text is None:
                return jsonify({"status": "error", "message": "dialogue required"}), 400
            result = self.dialogue_manager.update_dialogue(node_id, dialogue_text, translation, "" or "")
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/options/<node_id>", methods=["GET"])
        def admin_get_options(node_id):
            options = self.dialogue_manager.get_options_for_node(node_id)
            return jsonify({
                "status": "success",
                "data": [{"option_id": o[1], "option_text": o[2], "next_node_id": o[3], "feedback_type": o[4]} for o in options]
            }), 200

        @self.app.route("/api/admin/options/<node_id>", methods=["POST"])
        def admin_create_option(node_id):
            body = request.get_json()
            option_id = body.get("option_id")
            option_text = body.get("option_text", "")
            next_node_id = body.get("next_node_id", "")
            feedback_type = body.get("feedback_type", "neutral")
            if not option_id:
                return jsonify({"status": "error", "message": "option_id required"}), 400
            result = self.dialogue_manager.create_option(node_id, option_id, option_text, next_node_id, feedback_type)
            return jsonify({"status": "success", "data": result}), 201

        @self.app.route("/api/admin/options/<option_id>", methods=["PUT"])
        def admin_update_option(option_id):
            body = request.get_json()
            option_text = body.get("option_text", "")
            next_node_id = body.get("next_node_id", "")
            feedback_type = body.get("feedback_type")
            if not option_text and not next_node_id:
                return jsonify({"status": "error", "message": "option_text or next_node_id required"}), 400
            result = self.dialogue_manager.update_option(option_id, option_text, next_node_id, feedback_type or "neutral")
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/options/<option_id>", methods=["DELETE"])
        def admin_delete_option(option_id):
            result, success = self.dialogue_manager.delete_option(option_id)
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/vendors", methods=["GET"])
        def admin_get_vendors():
            vendors = self.vendor_manager.get_all_vendors()
            result = []
            for v in vendors:
                items = self.vendor_manager.get_items(v[0])
                result.append({
                    "vendor_id": v[0],
                    "node_id": v[1],
                    "npc_id": v[2],
                    "vendor_name": v[3],
                    "item_count": len(items)
                })
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/vendors", methods=["POST"])
        def admin_create_vendor():
            body = request.get_json()
            vendor_id = body.get("vendor_id")
            node_id = body.get("node_id")
            npc_id = body.get("npc_id")
            vendor_name = body.get("vendor_name")
            if not all([vendor_id, node_id, npc_id, vendor_name]):
                return jsonify({"status": "error", "message": "vendor_id, node_id, npc_id, vendor_name required"}), 400
            result = self.vendor_manager.create_vendor(vendor_id, node_id, npc_id, vendor_name)
            return jsonify({"status": "success", "data": result}), 201

        @self.app.route("/api/admin/vendors/<vendor_id>", methods=["PUT"])
        def admin_update_vendor(vendor_id):
            body = request.get_json()
            vendor_name = body.get("vendor_name")
            if not vendor_name:
                return jsonify({"status": "error", "message": "vendor_name required"}), 400
            result = self.vendor_manager.update_vendor(vendor_id, vendor_name)
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/vendors/<vendor_id>", methods=["DELETE"])
        def admin_delete_vendor(vendor_id):
            result, success = self.vendor_manager.delete_vendor(vendor_id)
            if not success:
                return jsonify({"status": "error", "message": result.get("error")}), 400
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/items/<vendor_id>", methods=["GET"])
        def admin_get_items(vendor_id):
            items = self.vendor_manager.get_items(vendor_id)
            return jsonify({
                "status": "success",
                "data": [{"vendor_id": i[0], "item_id": i[1], "item_name": i[2], "item_description": i[3], "item_value": i[4]} for i in items]
            }), 200

        @self.app.route("/api/admin/items/<vendor_id>", methods=["POST"])
        def admin_create_item(vendor_id):
            body = request.get_json()
            item_id = body.get("item_id")
            item_name = body.get("item_name")
            item_description = body.get("item_description", "")
            item_value = body.get("item_value", 0)
            if not item_id or not item_name:
                return jsonify({"status": "error", "message": "item_id and item_name required"}), 400
            result = self.vendor_manager.create_item(vendor_id, item_id, item_name, item_description, item_value)
            return jsonify({"status": "success", "data": result}), 201

        @self.app.route("/api/admin/items/<item_id>", methods=["PUT"])
        def admin_update_item(item_id):
            body = request.get_json()
            item_name = body.get("item_name")
            item_description = body.get("item_description")
            item_value = body.get("item_value")
            if not item_name:
                return jsonify({"status": "error", "message": "item_name required"}), 400
            result = self.vendor_manager.update_item(item_id, item_name, item_description or "", item_value or 0)
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/items/<item_id>", methods=["DELETE"])
        def admin_delete_item(item_id):
            result = self.vendor_manager.delete_item(item_id)
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/model/translate/<node_id>", methods=["POST"])
        def admin_model_generate_translate(node_id):
            body = request.get_json()
            output_lang = body.get("output_lang")
            dialogue_text = body.get("input_text")
            translation = self.hokTranslation.translate(dialogue_text, output_lang)
            dialogue = self.dialogue_manager.get_dialogue(node_id)
            result = self.dialogue_manager.update_dialogue(node_id, dialogue[0][2], translation, dialogue[0][4] or "")
            return jsonify({"status": "success", "data": result}), 200

        @self.app.route("/api/admin/model/tts/<node_id>", methods=["POST"])
        def admin_model_generate_tts(node_id):
            body = request.get_json()
            translation = body.get("translation_text")
            audio_src = self.hokTTS.generate_tts(node_id, translation)
            dialogue = self.dialogue_manager.get_dialogue(node_id)
            result = self.dialogue_manager.update_dialogue(node_id, dialogue[0][2], dialogue[0][3], audio_src or "")
            return jsonify({"status": "success", "data": result}), 200

def select_launch_mode():
    prompt = '''
Select launch mode...
        
> Press 0 | Launch in default mode
> Press 1 | Launch in test mode
> Press 2 | Launch in lesson mode
'''      
    mode = input(prompt)
    match mode:
        case "0":
            return 0
        case "1":
            return 1
        case "2":
            return 2
        case _:
            raise Exception("Error, mode selected is invalid.") 

if __name__ == "__main__":
    # Cloud hosts (like Railway) provide PORT and cannot handle interactive input.
    port = int(os.environ.get("PORT", 8000))

    # Force lesson mode in cloud; keep local interactive launcher for development.
    mode = 2 if "PORT" in os.environ else select_launch_mode()

    app_instance = App(mode)
    app_instance.run(host="0.0.0.0", port=port, debug=False)