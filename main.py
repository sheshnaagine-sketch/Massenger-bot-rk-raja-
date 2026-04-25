/**
 * RK RAJA BOT GROUP NAME LOCKER 
 * * Prerequisites:
 * 1. Install Node.js on your computer/server.
 * 2. Run: npm init -y
 * 3. Run: npm install fca-unofficial fs
 * 4. You need an 'appstate.json' file in the same folder. This contains 
 * your Facebook session cookies. (It is highly recommended to use a 
 * dummy/fake Facebook account for this, NOT your main account).
 */

const login = require("fca-unofficial");
const fs = require("fs");

// This object stores our locked settings in memory.
// In a real bot, you'd save this to a database or JSON file so it isn't lost on restart.
let lockedSettings = {};

// Load your Facebook session cookies
let appState;
try {
    appState = JSON.parse(fs.readFileSync('appstate.json', 'utf8'));
} catch (err) {
    console.error("Error: Could not find appstate.json. Please generate your session cookies.");
    process.exit(1);
}

login({ appState: appState }, (err, api) => {
    if (err) return console.error("Login failed:", err);

    console.log("Bot logged in successfully! Listening for messages and events...");

    // Listen to all incoming messages and events
    api.listenMqtt((err, event) => {
        if (err) return console.error(err);

        const threadID = event.threadID;

        // Initialize settings for this thread if they don't exist
        if (!lockedSettings[threadID]) {
            lockedSettings[threadID] = {
                lockedName: null,
                lockedNicknames: {}, // Format: { "userID": "Nickname" }
                nameLocked: false,
                nicknamesLocked: false
            };
        }

        const settings = lockedSettings[threadID];

        // ==========================================
        // 1. HANDLE TEXT COMMANDS (To activate locks)
        // ==========================================
        if (event.type === "message" && event.body) {
            const message = event.body.toLowerCase();

            // Command: /lockname [Name]
            if (message.startsWith("/lockname ")) {
                const newName = event.body.substring(10).trim();
                settings.lockedName = newName;
                settings.nameLocked = true;
                
                api.setTitle(newName, threadID, (err) => {
                    if (!err) api.sendMessage(`🔒 Group name has been locked to: "${newName}"`, threadID);
                });
            }

            // Command: /unlockname
            if (message === "/unlockname") {
                settings.nameLocked = false;
                api.sendMessage("🔓 Group name unlocked.", threadID);
            }

            // Command: /locknick [uid] [Nickname]
            // Example: /locknick 1000123456789 The Boss
            if (message.startsWith("/locknick ")) {
                const parts = event.body.split(" ");
                if (parts.length >= 3) {
                    const targetUID = parts[1];
                    const targetNick = parts.slice(2).join(" ");
                    
                    settings.lockedNicknames[targetUID] = targetNick;
                    settings.nicknamesLocked = true;
                    
                    api.changeNickname(targetNick, threadID, targetUID, (err) => {
                        if (!err) api.sendMessage(`🔒 Nickname locked for user!`, threadID);
                    });
                }
            }
        }

        // ==========================================
        // 2. HANDLE EVENTS (The Anti-Change System)
        // ==========================================
        if (event.type === "event") {
            
            // --- A. PREVENT GROUP NAME CHANGES ---
            if (event.logMessageType === "log:thread-name") {
                const newName = event.logMessageData.name;
                
                // If the name is locked and the new name isn't the locked name
                if (settings.nameLocked && settings.lockedName && newName !== settings.lockedName) {
                    console.log(`Reverting name in ${threadID} back to ${settings.lockedName}`);
                    
                    // Change it right back!
                    api.setTitle(settings.lockedName, threadID, (err) => {
                        if (!err) {
                            api.sendMessage("⚠️ Group name is locked. You cannot change it.", threadID);
                        }
                    });
                }
            }

            // --- B. PREVENT NICKNAME CHANGES ---
            if (event.logMessageType === "log:user-nickname") {
                const changedUID = event.logMessageData.participant_id;
                const newNick = event.logMessageData.nickname;

                // If this specific user has a locked nickname
                if (settings.nicknamesLocked && settings.lockedNicknames[changedUID]) {
                    const enforcedNick = settings.lockedNicknames[changedUID];
                    
                    if (newNick !== enforcedNick) {
                        console.log(`Reverting nickname for ${changedUID}`);
                        
                        // Change it right back!
                        api.changeNickname(enforcedNick, threadID, changedUID, (err) => {
                            if (!err) {
                                api.sendMessage("⚠️ That nickname is locked.", threadID);
                            }
                        });
                    }
                }
            }

            // --- C. PREVENT PHOTO CHANGES ---
            // Group photo locking is handled via "log:thread-icon"
            if (event.logMessageType === "log:thread-icon") {
                // To revert an image, you have to upload the image file again using api.changeGroupImage()
                // You would need to store the fs.createReadStream('locked_image.png') in your settings.
                // For simplicity, we just send a warning message here.
                api.sendMessage("⚠️ Please do not change the group photo!", threadID);
            }
        }
    });
});
