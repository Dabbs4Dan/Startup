import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  View, Text, TextInput, Pressable, ScrollView, Modal, SafeAreaView,
  KeyboardAvoidingView, Platform, Linking, StatusBar, useColorScheme, Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const LABELS = {
  guide: { name: 'Guide', emoji: '💡', c: '#f5c518', bg: '#fff6cf', bgD: '#3a3215' },
  business: { name: 'Business', emoji: '💲', c: '#2fa866', bg: '#dcf5e6', bgD: '#173326' },
  experience: { name: 'Experience', emoji: '✈️', c: '#3a8ee6', bg: '#dcebfc', bgD: '#172a40' },
  art: { name: 'Art', emoji: '🌈', c: '#a46bff', bg: '#f6ecff', bgD: '#2c2140' },
};
const RAINBOW = ['#ff5e5e', '#ffb03b', '#ffe14d', '#4cd97b', '#4aa8ff', '#a46bff'];

// World English Bible (public domain). Each opens the same passage on Bible.com.
const VERSES = [
  ['Jeremiah 29:11', 'JER.29.11', '“For I know the thoughts that I think toward you,” says Yahweh, “thoughts of peace, and not of evil, to give you hope and a future.”'],
  ['Philippians 4:13', 'PHP.4.13', 'I can do all things through Christ, who strengthens me.'],
  ['Proverbs 3:5–6', 'PRO.3.5-6', 'Trust in Yahweh with all your heart, and don’t lean on your own understanding. In all your ways acknowledge him, and he will make your paths straight.'],
  ['Isaiah 40:31', 'ISA.40.31', 'But those who wait for Yahweh will renew their strength. They will mount up with wings like eagles. They will run, and not be weary. They will walk, and not faint.'],
  ['Joshua 1:9', 'JOS.1.9', 'Be strong and courageous. Don’t be afraid. Don’t be dismayed, for Yahweh your God is with you wherever you go.'],
  ['Psalm 46:10', 'PSA.46.10', 'Be still, and know that I am God.'],
  ['Matthew 6:33', 'MAT.6.33', 'But seek first God’s Kingdom and his righteousness; and all these things will be given to you as well.'],
  ['Romans 8:28', 'ROM.8.28', 'We know that all things work together for good for those who love God, for those who are called according to his purpose.'],
  ['Psalm 23:1', 'PSA.23.1', 'Yahweh is my shepherd; I shall lack nothing.'],
  ['Colossians 3:23', 'COL.3.23', 'And whatever you do, work heartily, as for the Lord, and not for men.'],
  ['Proverbs 16:3', 'PRO.16.3', 'Commit your deeds to Yahweh, and your plans shall succeed.'],
  ['2 Timothy 1:7', '2TI.1.7', 'For God didn’t give us a spirit of fear, but of power, love, and self-control.'],
  ['Psalm 119:105', 'PSA.119.105', 'Your word is a lamp to my feet, and a light for my path.'],
  ['Lamentations 3:22–23', 'LAM.3.22-23', 'His mercies don’t fail. They are new every morning. Great is your faithfulness.'],
  ['Matthew 11:28', 'MAT.11.28', 'Come to me, all you who labor and are heavily burdened, and I will give you rest.'],
  ['Psalm 37:4', 'PSA.37.4', 'Also delight yourself in Yahweh, and he will give you the desires of your heart.'],
  ['Isaiah 41:10', 'ISA.41.10', 'Don’t you be afraid, for I am with you. Don’t be dismayed, for I am your God. I will strengthen you. Yes, I will help you.'],
  ['Philippians 4:6', 'PHP.4.6', 'In nothing be anxious, but in everything, by prayer and petition with thanksgiving, let your requests be made known to God.'],
  ['James 1:5', 'JAS.1.5', 'But if any of you lacks wisdom, let him ask of God, who gives to all liberally and without reproach, and it will be given to him.'],
  ['Ecclesiastes 3:1', 'ECC.3.1', 'For everything there is a season, and a time for every purpose under heaven.'],
  ['Ephesians 2:10', 'EPH.2.10', 'For we are his workmanship, created in Christ Jesus for good works, which God prepared before that we would walk in them.'],
  ['Psalm 90:12', 'PSA.90.12', 'So teach us to count our days, that we may gain a heart of wisdom.'],
  ['Hebrews 11:1', 'HEB.11.1', 'Now faith is assurance of things hoped for, proof of things not seen.'],
  ['Galatians 6:9', 'GAL.6.9', 'Let’s not be weary in doing good, for we will reap in due season if we don’t give up.'],
  ['Micah 6:8', 'MIC.6.8', 'What does Yahweh require of you, but to act justly, to love mercy, and to walk humbly with your God?'],
  ['Psalm 118:24', 'PSA.118.24', 'This is the day that Yahweh has made. We will rejoice and be glad in it!'],
  ['Proverbs 21:5', 'PRO.21.5', 'The plans of the diligent surely lead to profit.'],
  ['1 Peter 5:7', '1PE.5.7', 'Casting all your worries on him, because he cares for you.'],
  ['Romans 12:2', 'ROM.12.2', 'Don’t be conformed to this world, but be transformed by the renewing of your mind.'],
  ['Psalm 19:1', 'PSA.19.1', 'The heavens declare the glory of God. The expanse shows his handiwork.'],
  ['Habakkuk 2:2', 'HAB.2.2', 'Write the vision, and make it plain on tablets, that he who runs may read it.'],
];

const KEY = 'dailybread.notes.v1';

function todayVerse() {
  const n = new Date();
  const day = Math.floor((Date.UTC(n.getFullYear(), n.getMonth(), n.getDate()) - Date.UTC(2026, 0, 1)) / 864e5);
  return VERSES[((day % VERSES.length) + VERSES.length) % VERSES.length];
}

function useTheme() {
  const dark = useColorScheme() === 'dark';
  return {
    dark,
    bg: dark ? '#16131c' : '#ffffff',
    ink: dark ? '#efe9f3' : '#2b2233',
    soft: dark ? '#a99fb3' : '#7a6e84',
    card: dark ? '#211d29' : '#ffffff',
    line: dark ? '#2f2a38' : '#ece6ef',
    plum: dark ? '#d9c6ea' : '#4a2d5c',
    dawn: dark ? '#2e2541' : '#f6dcd8',
    dawn2: dark ? '#3a2a3f' : '#fbe7d6',
    onPlum: dark ? '#16131c' : '#ffffff',
  };
}

function Tag({ k, t }) {
  const l = LABELS[k] || LABELS.guide;
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', backgroundColor: t.dark ? l.bgD : l.bg, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 3 }}>
      <Text style={{ fontSize: 13, fontWeight: '700', color: t.ink }}>{l.emoji} {l.name}</Text>
    </View>
  );
}

function Stripe({ k }) {
  if (k === 'art') {
    return (
      <View style={{ width: 6, borderTopLeftRadius: 18, borderBottomLeftRadius: 18, overflow: 'hidden' }}>
        {RAINBOW.map((c) => <View key={c} style={{ flex: 1, backgroundColor: c }} />)}
      </View>
    );
  }
  return <View style={{ width: 6, borderTopLeftRadius: 18, borderBottomLeftRadius: 18, backgroundColor: (LABELS[k] || LABELS.guide).c }} />;
}

function NoteCard({ n, t, onToggle, onOpen }) {
  const d = new Date(n.created).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  return (
    <View style={{ flexDirection: 'row', backgroundColor: t.card, borderRadius: 18, borderWidth: 1, borderColor: t.line, marginBottom: 10, overflow: 'hidden' }}>
      <Stripe k={n.label} />
      <Pressable onPress={onToggle} hitSlop={10} style={{ padding: 14, paddingRight: 4 }} accessibilityLabel={n.done ? 'Mark not done' : 'Mark done'}>
        <View style={{ width: 28, height: 28, borderRadius: 14, borderWidth: 2, borderColor: n.done ? t.soft : t.line, backgroundColor: n.done ? t.soft : 'transparent', alignItems: 'center', justifyContent: 'center' }}>
          {n.done ? <Text style={{ color: '#fff', fontWeight: '800' }}>✓</Text> : null}
        </View>
      </Pressable>
      <Pressable onPress={onOpen} style={{ flex: 1, padding: 14, paddingLeft: 8 }}>
        <Text style={{ fontSize: 16, lineHeight: 23, color: n.done ? t.soft : t.ink, textDecorationLine: n.done ? 'line-through' : 'none', marginBottom: 8 }}>{n.text}</Text>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <Tag k={n.label} t={t} />
          <Text style={{ fontSize: 13, color: t.soft }}>{d}</Text>
        </View>
      </Pressable>
    </View>
  );
}

export default function App() {
  const t = useTheme();
  const verse = useMemo(todayVerse, []);
  const [notes, setNotes] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [filter, setFilter] = useState('all');
  const [showDone, setShowDone] = useState(false);

  const [open, setOpen] = useState(false);
  const [editId, setEditId] = useState(null);
  const [text, setText] = useState('');
  const [label, setLabel] = useState('guide');
  const [menu, setMenu] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    AsyncStorage.getItem(KEY).then((raw) => {
      try { setNotes(raw ? JSON.parse(raw) : []); } catch (e) { setNotes([]); }
      setLoaded(true);
    }).catch(() => setLoaded(true));
  }, []);

  const save = (next) => {
    setNotes(next);
    AsyncStorage.setItem(KEY, JSON.stringify(next)).catch(() => {});
  };

  const openSheet = (n) => {
    setEditId(n ? n.id : null);
    setText(n ? n.text : '');
    setLabel(n ? n.label : (filter !== 'all' ? filter : 'guide'));
    setMenu(false);
    setOpen(true);
  };
  const close = () => { setOpen(false); setMenu(false); };

  const commit = () => {
    const body = text.trim();
    if (!body) { close(); return; }
    const now = Date.now();
    if (editId) save(notes.map((n) => (n.id === editId ? { ...n, text: body, label, updated: now } : n)));
    else save([{ id: 'n' + now.toString(36), text: body, label, done: false, created: now, updated: now }, ...notes]);
    close();
  };

  const remove = () => {
    Alert.alert('Delete this note?', '', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: () => { save(notes.filter((n) => n.id !== editId)); close(); } },
    ]);
  };

  const toggle = (id) => save(notes.map((n) => (n.id === id ? { ...n, done: !n.done, updated: Date.now() } : n)));

  const shown = notes.filter((n) => filter === 'all' || n.label === filter).sort((a, b) => b.created - a.created);
  const openList = shown.filter((n) => !n.done);
  const doneList = shown.filter((n) => n.done);
  const today = new Date();
  const lab = LABELS[label];

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: t.bg }}>
      <StatusBar barStyle={t.dark ? 'light-content' : 'dark-content'} />
      <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 140 }}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', paddingHorizontal: 4, paddingBottom: 12 }}>
          <Text style={{ fontSize: 30, fontWeight: '600', color: t.plum, fontFamily: Platform.OS === 'ios' ? 'Georgia' : 'serif' }}>
            {today.toLocaleDateString(undefined, { month: 'long', day: 'numeric' })}
          </Text>
          <Text style={{ fontSize: 14, color: t.soft }}>{today.toLocaleDateString(undefined, { weekday: 'long' })}</Text>
        </View>

        <View style={{ backgroundColor: t.dawn, borderRadius: 24, padding: 22, overflow: 'hidden' }}>
          <View style={{ position: 'absolute', right: -40, top: -40, width: 160, height: 160, borderRadius: 80, backgroundColor: t.dawn2, opacity: 0.9 }} />
          <View style={{ position: 'absolute', right: -10, top: -10, width: 90, height: 90, borderRadius: 45, backgroundColor: t.dark ? '#4a3a52' : '#fff2e2' }} />
          <Text style={{ fontSize: 13, fontWeight: '700', color: t.plum, opacity: 0.8 }}>Verse of the day</Text>
          <Text style={{ fontSize: 21, lineHeight: 30, fontStyle: 'italic', color: t.plum, marginVertical: 12, fontFamily: Platform.OS === 'ios' ? 'Georgia' : 'serif' }}>{verse[2]}</Text>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
            <Text style={{ fontWeight: '700', color: t.plum }}>{verse[0]} · WEB</Text>
            <Pressable onPress={() => Linking.openURL('https://www.bible.com/bible/206/' + verse[1] + '.WEB')} style={{ backgroundColor: t.dark ? 'rgba(255,255,255,0.12)' : 'rgba(255,255,255,0.6)', borderRadius: 999, paddingHorizontal: 14, paddingVertical: 8 }}>
              <Text style={{ fontWeight: '700', color: t.plum, fontSize: 14 }}>Read on Bible.com ↗</Text>
            </Pressable>
          </View>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 18, marginBottom: 6 }} contentContainerStyle={{ gap: 8, paddingHorizontal: 2 }}>
          {[['all', 'All'], ...Object.entries(LABELS).map(([k, l]) => [k, l.emoji + ' ' + l.name])].map(([k, name]) => {
            const on = filter === k;
            return (
              <Pressable key={k} onPress={() => setFilter(k)} style={{ borderRadius: 999, borderWidth: 1, borderColor: on ? t.plum : t.line, backgroundColor: on ? t.plum : t.card, paddingHorizontal: 14, paddingVertical: 9 }}>
                <Text style={{ fontWeight: '600', fontSize: 14, color: on ? t.onPlum : t.ink }}>{name}</Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 14, marginBottom: 10, paddingHorizontal: 4 }}>
          <Text style={{ fontSize: 20, color: t.plum, fontFamily: Platform.OS === 'ios' ? 'Georgia' : 'serif' }}>Action items</Text>
          {openList.length ? <Text style={{ fontSize: 13, fontWeight: '600', color: t.soft }}>{openList.length} open</Text> : null}
        </View>

        {loaded && openList.length === 0 ? (
          <View style={{ borderWidth: 1.5, borderStyle: 'dashed', borderColor: t.line, borderRadius: 18, padding: 30, alignItems: 'center' }}>
            <Text style={{ fontSize: 19, color: t.plum, marginBottom: 4, fontFamily: Platform.OS === 'ios' ? 'Georgia' : 'serif' }}>{filter === 'all' ? 'A fresh page' : 'Nothing here yet'}</Text>
            <Text style={{ color: t.soft, textAlign: 'center' }}>Tap the + button below to write your first note.</Text>
          </View>
        ) : null}
        {openList.map((n) => <NoteCard key={n.id} n={n} t={t} onToggle={() => toggle(n.id)} onOpen={() => openSheet(n)} />)}

        {doneList.length ? (
          <>
            <Pressable onPress={() => setShowDone(!showDone)} style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 14, marginBottom: 10, paddingHorizontal: 4 }}>
              <Text style={{ fontSize: 20, color: t.plum, fontFamily: Platform.OS === 'ios' ? 'Georgia' : 'serif' }}>Done ✔︎ {showDone ? '▾' : '▸'}</Text>
              <Text style={{ fontSize: 13, fontWeight: '600', color: t.soft }}>{doneList.length}</Text>
            </Pressable>
            {showDone ? doneList.map((n) => <NoteCard key={n.id} n={n} t={t} onToggle={() => toggle(n.id)} onOpen={() => openSheet(n)} />) : null}
          </>
        ) : null}
      </ScrollView>

      <Pressable onPress={() => openSheet(null)} accessibilityLabel="Add a note"
        style={({ pressed }) => ({ position: 'absolute', alignSelf: 'center', bottom: 34, width: 66, height: 66, borderRadius: 33, backgroundColor: t.plum, alignItems: 'center', justifyContent: 'center', transform: [{ scale: pressed ? 0.94 : 1 }], shadowColor: '#4a2d5c', shadowOpacity: 0.35, shadowRadius: 14, shadowOffset: { width: 0, height: 8 }, elevation: 8 })}>
        <Text style={{ color: t.onPlum, fontSize: 38, lineHeight: 42, fontWeight: '300' }}>+</Text>
      </Pressable>

      <Modal visible={open} animationType="slide" presentationStyle="pageSheet" onRequestClose={close}>
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1, backgroundColor: t.bg }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 14, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: t.line, zIndex: 2 }}>
            <Pressable onPress={close} hitSlop={10}><Text style={{ fontSize: 17, fontWeight: '600', color: t.plum }}>Cancel</Text></Pressable>
            <Pressable onPress={() => setMenu(!menu)} style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: t.dark ? lab.bgD : lab.bg, borderRadius: 999, paddingHorizontal: 14, paddingVertical: 9 }}>
              <View style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: lab.c, marginRight: 8 }} />
              <Text style={{ fontSize: 15, fontWeight: '700', color: t.ink }}>{lab.emoji} {lab.name}  ▾</Text>
            </Pressable>
            <Pressable onPress={commit} style={{ backgroundColor: t.plum, borderRadius: 999, paddingHorizontal: 18, paddingVertical: 9 }}>
              <Text style={{ fontSize: 16, fontWeight: '700', color: t.onPlum }}>Save</Text>
            </Pressable>
          </View>

          {menu ? (
            <View style={{ position: 'absolute', top: 64, alignSelf: 'center', width: 220, backgroundColor: t.card, borderRadius: 16, borderWidth: 1, borderColor: t.line, padding: 6, zIndex: 5, shadowColor: '#000', shadowOpacity: 0.18, shadowRadius: 16, shadowOffset: { width: 0, height: 8 }, elevation: 10 }}>
              {Object.entries(LABELS).map(([k, l]) => (
                <Pressable key={k} onPress={() => { setLabel(k); setMenu(false); inputRef.current && inputRef.current.focus(); }}
                  style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: t.dark ? l.bgD : l.bg, borderRadius: 12, paddingHorizontal: 12, paddingVertical: 12, marginVertical: 2, borderWidth: label === k ? 2 : 0, borderColor: l.c }}>
                  {k === 'art'
                    ? <View style={{ width: 12, height: 12, borderRadius: 6, overflow: 'hidden', flexDirection: 'row', marginRight: 10 }}>{RAINBOW.map((c) => <View key={c} style={{ flex: 1, backgroundColor: c }} />)}</View>
                    : <View style={{ width: 12, height: 12, borderRadius: 6, backgroundColor: l.c, marginRight: 10 }} />}
                  <Text style={{ fontSize: 16, fontWeight: '700', color: t.ink }}>{l.emoji} {l.name}</Text>
                </Pressable>
              ))}
            </View>
          ) : null}

          <TextInput
            ref={inputRef}
            value={text}
            onChangeText={setText}
            autoFocus
            multiline
            placeholder="What's on your heart today?"
            placeholderTextColor={t.soft}
            style={{ flex: 1, fontSize: 17, lineHeight: 26, color: t.ink, padding: 18, textAlignVertical: 'top' }}
          />
          {editId ? (
            <Pressable onPress={remove} style={{ alignItems: 'center', paddingVertical: 12 }}>
              <Text style={{ color: '#d4485a', fontWeight: '600', fontSize: 15 }}>Delete note</Text>
            </Pressable>
          ) : null}
        </KeyboardAvoidingView>
      </Modal>
    </SafeAreaView>
  );
}
