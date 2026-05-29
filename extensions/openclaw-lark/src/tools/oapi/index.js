"use strict";
/**
 * Copyright (c) 2026 ByteDance Ltd. and/or its affiliates
 * SPDX-License-Identifier: MIT
 *
 * OAPI Tools Index
 *
 * This module registers all tools that directly use Feishu Open API (OAPI).
 * These tools are placed here to distinguish them from MCP-based tools.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.registerOapiTools = registerOapiTools;
const index_1 = require("../tat/im/index.js");
const index_5 = require("./common/index.js");
const index_10 = require("./chat/index.js");
const index_11 = require("./im/index.js");
function registerOapiTools(api) {
    // Common tools
    (0, index_5.registerGetUserTool)(api);
    (0, index_5.registerSearchUserTool)(api);
    // Chat tools
    (0, index_10.registerFeishuChatTools)(api);
    // IM tools (user identity)
    (0, index_11.registerFeishuImTools)(api);
    // IM tools (bot identity)
    (0, index_1.registerFeishuImTools)(api);
    api.logger.debug?.('Registered OAPI tools (common, chat, im)');
}
