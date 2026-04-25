const login = require("fca-unofficial");
const fs = require("fs");

// Load saved settings
let lockedSettings = {};
if (fs.existsSync("data.json")) {
    lockedSettings = JSON.parse(fs.readFileSync("data.json"));
}

// Save function
function saveData() {
    fs.writeFileSync("data.json", JSON.stringify(lockedSettings, null, 2));
}

// Load appstate
let appState;
try {
    appState = JSON.parse(fs.readFileSync('appstate.json', 'utf8'));
} catch (err) {
    console.error("appstate.json not found!");
    process.exit(1);
}

login({ appState }, (err, api) => {
    if (err) return console.error(err);

    console.log("✅ Bot started!");

    api.listenMqtt((err, event) => {
        if (err) return console.error(err);

        const threadID = event.threadID;

        if (!lockedSettings[threadID]) {
            lockedSettings[threadID] = {
                lockedName: null,
                lockedNicknames: {},
                nameLocked: false,
                nicknamesLocked: false
            };
        }

        const settings = lockedSettings[threadID];

        // COMMANDS
        if (event.type === "message" && event.body) {
            const msg = event.body.toLowerCase();

            // Lock name
            if (msg.startsWith("/lockname ")) {
                const name = event.body.substring(10).trim();
                settings.lockedName = name;
                settings.nameLocked = true;

                api.setTitle(name, threadID);
                api.sendMessage("🔒 Name locked!", threadID);
                saveData();
            }

            // Unlock name
            if (msg === "/unlockname") {
                settings.nameLocked = false;
                api.sendMessage("🔓 Name unlocked!", threadID);
                saveData();
            }

            // Lock nickname
            if (msg.startsWith("/locknick ")) {
                const parts = event.body.split(" ");
                const uid = parts[1];
                const nick = parts.slice(2).join(" ");

                settings.lockedNicknames[uid] = nick;
                settings.nicknamesLocked = true;

                api.changeNickname(nick, threadID, uid);
                api.sendMessage("🔒 Nick locked!", threadID);
                saveData();
            }
        }

        // EVENTS
        if (event.type === "event") {

            // Name change
            if (event.logMessageType === "log:thread-name") {
                if (settings.nameLocked && settings.lockedName) {
                    api.setTitle(settings.lockedName, threadID);
                    api.sendMessage("⚠️ Name is locked!", threadID);
                }
            }

            // Nickname change
            if (event.logMessageType === "log:user-nickname") {
                const uid = event.logMessageData.participant_id;

                if (settings.lockedNicknames[uid]) {
                    api.changeNickname(
                        settings.lockedNicknames[uid],
                        threadID,
                        uid
                    );
                    api.sendMessage("⚠️ Nick locked!", threadID);
                }
            }
        }
    });
});
