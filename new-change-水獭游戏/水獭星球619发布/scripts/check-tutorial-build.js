const fs = require("fs");

const version = "20260619-retell-bg1";
const files = {
  html: fs.readFileSync("index.html", "utf8"),
  main: fs.readFileSync("assets/index-DbNKf0P0.js", "utf8"),
  parkour: fs.readFileSync("assets/SectionParkour-Ba-Fk1Jk.js", "utf8"),
  nav: fs.readFileSync("otterlantis-navigation.js", "utf8"),
  loader: fs.readFileSync("otterlantis-loader.js", "utf8"),
  audio: fs.readFileSync("otterlantis-audio.js", "utf8"),
};

const failures = [];

function expectContains(name, text, needle) {
  if (!text.includes(needle)) failures.push(`${name} is missing ${needle}`);
}

function expectMissing(name, text, needle) {
  if (text.includes(needle)) failures.push(`${name} still contains ${needle}`);
}

expectContains("index.html", files.html, `/assets/index-DbNKf0P0.js?v=${version}`);
expectContains("index.html", files.html, `/otterlantis-story-tts.js?v=${version}`);
expectMissing("index.html", files.html, `/assets/SectionParkour-Ba-Fk1Jk.js?v=${version}`);
expectContains("index.html", files.html, `/otterlantis-navigation.js?v=${version}`);
expectContains("index.html", files.html, `/otterlantis-overrides.css?v=${version}`);
expectContains("index.html", files.html, `/otterlantis-loader.js?v=${version}`);
expectContains("index.html", files.html, `/otterlantis-audio.js?v=${version}`);
expectContains("assets/index-DbNKf0P0.js", files.main, `./SectionParkour-Ba-Fk1Jk.js?v=${version}`);
expectContains("otterlantis-navigation.js", files.nav, `/assets/SectionParkour-Ba-Fk1Jk.js?v=${version}`);
expectContains("assets/index-DbNKf0P0.js", files.main, "URLSearchParams(window.location.search)");
expectContains("assets/index-DbNKf0P0.js", files.main, 'searchParams.set("lang",');
expectContains("assets/index-DbNKf0P0.js", files.main, "document.documentElement.lang");
expectContains("otterlantis-loader.js", files.loader, "Otter is landing on the path...");
expectContains("otterlantis-navigation.js", files.nav, "Otter is landing on the path...");
expectMissing("otterlantis-loader.js", files.loader, "otter-global-landing-spinner");
expectMissing("otterlantis-navigation.js", files.nav, "otter-landing-spinner");
expectMissing("assets/index-DbNKf0P0.js", files.main, "animate-spin mb-5");
expectMissing("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, "animate-spin mb-5");
expectContains("otterlantis-audio.js", files.audio, "Music");
expectContains("otterlantis-audio.js", files.audio, "Turn music off");
expectContains("otterlantis-audio.js", files.audio, "function warmupAndTryAutoplay()");
expectContains("otterlantis-audio.js", files.audio, "attachUnlockListeners()");
expectContains("otterlantis-audio.js", files.audio, "tracks[trackName].load()");
expectContains("otterlantis-audio.js", files.audio, "audio.autoplay = true");
expectContains("otterlantis-audio.js", files.audio, "attachUnlockListeners();\n    warmupAndTryAutoplay();");
expectContains("otterlantis-audio.js", files.audio, 'document.addEventListener("click", markGestureAndPlay');
expectContains("otterlantis-audio.js", files.audio, 'document.addEventListener("mousedown", markGestureAndPlay');
expectContains("otterlantis-audio.js", files.audio, 'document.addEventListener("pointerup", markGestureAndPlay');
expectContains("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, "aU={zh:");
expectContains("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, "Always reply in English only");
expectContains("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, "content:aU[e][xe]");
expectMissing("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, "content:aU[xe]");
expectContains("assets/index-DbNKf0P0.js", files.main, "content:RA[l]");
expectContains("assets/index-DbNKf0P0.js", files.main, "fy[l]");
expectContains("assets/index-DbNKf0P0.js", files.main, "Reply must be ≤14 words, natural spoken English");
expectContains("assets/index-DbNKf0P0.js", files.main, "Reply must be one natural spoken sentence");
expectContains("assets/index-DbNKf0P0.js", files.main, 'Tap to continue!');
expectContains("assets/index-DbNKf0P0.js", files.main, 'startsWith("en")');
expectMissing("assets/index-DbNKf0P0.js", files.main, 'children:"点一下继续！"');
expectContains("assets/index-DbNKf0P0.js", files.main, 'bg.webp?v=20260619-retell-bg');
expectMissing("assets/index-DbNKf0P0.js", files.main, '`${xe}/bg.webp?v=202606112151`');

for (const [name, text] of Object.entries(files)) {
  expectMissing(name, text, "20260618-landingbg");
  expectMissing(name, text, "20260618-anymove");
  expectMissing(name, text, "20260618-scrollfix");
}

expectMissing(
  "assets/SectionParkour-Ba-Fk1Jk.js",
  files.parkour,
  "const l=ON[r],c=l.Icon,u=!0,h=r===e;"
);
expectMissing(
  "assets/SectionParkour-Ba-Fk1Jk.js",
  files.parkour,
  "function XN(s){return s.inputDirection?{currentDirectionIndex:s.currentDirectionIndex,isComplete:!0"
);
expectContains("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, "triedDirections");
expectContains("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, "isComplete:e.size>=2");
expectContains("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, "currentDirection:null");
expectContains("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, 'lang:e');
expectContains("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, 'e==="zh"?"跟着箭头去第一颗星星！":"Follow the arrow to the first star!"');
expectContains("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, 'e==="zh"?"往星星那里走！":"Walk toward the star!"');
expectContains("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, 'e==="zh"?"砰！":"Bump!"');
expectContains("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, 'startsWith("en")?s.id===0?"Bump me!":"Touch the star!"');
expectContains("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, 'startsWith("en")?"Avoid the box":"避开箱子"');
expectMissing("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, 'children:"跟着箭头去第一颗星星！"');
expectMissing("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, 'children:"往星星那里走！"');
expectMissing("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, 'Hr("box","砰！")');
expectMissing("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, 'text:s.id===0?"撞我！":"碰到星星！"');
expectMissing("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, 'text:"避开箱子"');
expectMissing("assets/SectionParkour-Ba-Fk1Jk.js", files.parkour, "154.85.55.67");
expectContains(
  "assets/SectionParkour-Ba-Fk1Jk.js",
  files.parkour,
  "https://api.otterlantis.com/api/fish-tts"
);

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log("tutorial build checks passed");
