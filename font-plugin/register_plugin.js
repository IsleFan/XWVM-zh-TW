// Registers XwvmChineseFont.dll in an XWVM (Unity) data folder so Unity loads it at startup.
// macOS's built-in JavaScript (JXA), so no Python or other tools are needed:
//
//   osascript -l JavaScript register_plugin.js <Data folder> [--uninstall]
//
//   ScriptingAssemblies.json      : adds the assembly (type 16 = user assembly)
//   RuntimeInitializeOnLoads.json : calls FallbackFontLoader.Init before the first scene
// Any previous registration is removed first, so running it again is safe.
ObjC.import('Foundation');

var ASSEMBLY = 'XwvmChineseFont';
var INIT_ENTRY = {
    assemblyName: ASSEMBLY,
    nameSpace: 'XwvmChineseFont',
    className: 'FallbackFontLoader',
    methodName: 'Init',
    loadTypes: 1, // RuntimeInitializeLoadType.BeforeSceneLoad
    isUnityClass: false
};

function readJson(path) {
    var text = $.NSString.stringWithContentsOfFileEncodingError(path, $.NSUTF8StringEncoding, null);
    if (!text || text.isNil()) {
        throw new Error('Not an XWVM data folder (cannot read ' + path + ')');
    }
    return JSON.parse(text.js.replace(/^﻿/, ''));
}

function writeJson(path, value) {
    if (!$(JSON.stringify(value)).writeToFileAtomicallyEncodingError(path, true, $.NSUTF8StringEncoding, null)) {
        throw new Error('Cannot write ' + path);
    }
}

function run(argv) {
    var data = argv[0];
    var uninstall = argv.indexOf('--uninstall') >= 0;
    var dll = ASSEMBLY + '.dll';
    var assembliesPath = data + '/ScriptingAssemblies.json';
    var initPath = data + '/RuntimeInitializeOnLoads.json';

    var assemblies = readJson(assembliesPath);
    var inits = readJson(initPath);

    var names = [], types = [];
    for (var i = 0; i < assemblies.names.length; i++) {
        if (assemblies.names[i] !== dll) {
            names.push(assemblies.names[i]);
            types.push(assemblies.types[i]);
        }
    }
    inits.root = inits.root.filter(function (e) { return e.assemblyName !== ASSEMBLY; });

    if (!uninstall) {
        names.push(dll);
        types.push(16);
        inits.root.push(INIT_ENTRY);
    }
    assemblies.names = names;
    assemblies.types = types;

    writeJson(assembliesPath, assemblies);
    writeJson(initPath, inits);
    return (uninstall ? 'Removed from ' : 'Registered in ') + data;
}
