import { useEffect, useState } from "react";
import { ActivityIndicator, Alert, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import type { LearnerProfile, Progress, Scenario, TutorFeedback, VocabularyWord } from "@mengo/shared-types";
import { api } from "./src/api";

type Tab = "learn" | "review" | "profile";
type Message = { role: "You" | "Mengo"; text: string; secondary?: string };
const initialFeedback: TutorFeedback = { grammar: "Start a conversation to receive grammar feedback.", vocabulary: "Save helpful words to your review queue.", tones: "The mock coach gives deterministic tone tips.", pronunciation_score: 0 };

export default function App() {
  const [profile, setProfile] = useState<LearnerProfile | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [progress, setProgress] = useState<Progress | null>(null);
  const [tab, setTab] = useState<Tab>("learn");
  const [active, setActive] = useState<Scenario | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [line, setLine] = useState("你好，我叫 Alex。");
  const [messages, setMessages] = useState<Message[]>([]);
  const [feedback, setFeedback] = useState<TutorFeedback>(initialFeedback);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [p, s, pr] = await Promise.all([api.profile(), api.scenarios(), api.progress()]);
      setProfile(p); setScenarios(s); setProgress(pr);
    } catch (error) { Alert.alert("Could not reach Mengo", error instanceof Error ? error.message : "Check the local API URL."); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);

  const begin = async (scenario: Scenario) => {
    try { const session = await api.createSession(scenario.id); setActive(scenario); setSessionId(session.id); setMessages([{ role: "Mengo", text: scenario.prompt }]); }
    catch (error) { Alert.alert("Lesson unavailable", String(error)); }
  };
  const speak = async () => {
    if (!sessionId || !line.trim()) return;
    try {
      const result = await api.sendTurn(sessionId, line.trim());
      setMessages((old) => [...old, { role: "You", text: result.learner_transcript }, { role: "Mengo", text: result.tutor_response, secondary: result.tutor_pinyin }]);
      setFeedback(result.feedback); setLine("");
      if (result.session_completed) { await load(); Alert.alert("Scenario complete", "Your streak and minutes have been updated."); }
    } catch (error) { Alert.alert("Could not send practice", String(error)); }
  };
  const finishOnboarding = async () => {
    if (!profile) return;
    const saved = await api.saveProfile({ goal: profile.goal, level: profile.level, minutes_per_day: profile.minutes_per_day });
    setProfile(saved);
  };
  const saveWord = async (word: VocabularyWord) => { await api.saveWord(word); Alert.alert("Saved", `${word.hanzi} is in your review queue.`); };

  if (loading || !profile) return <SafeAreaView style={styles.center}><ActivityIndicator color="#D85B3F" /><Text>Opening Mengo…</Text></SafeAreaView>;
  if (!profile.onboarding_complete) return <SafeAreaView style={styles.safe}><ScrollView contentContainerStyle={styles.page}><Text style={styles.logo}>mengo</Text><Text style={styles.h1}>Mandarin for your real life.</Text><Text style={styles.muted}>Set a light, English-first study plan. You can change it anytime.</Text><Text style={styles.label}>Your goal</Text><TextInput value={profile.goal} onChangeText={(goal) => setProfile({ ...profile, goal })} style={styles.input} /><Text style={styles.label}>Level</Text><View style={styles.row}>{(["beginner", "elementary", "intermediate"] as const).map((level) => <Chip key={level} title={level} active={profile.level === level} onPress={() => setProfile({ ...profile, level })} />)}</View><Text style={styles.label}>Minutes a day</Text><View style={styles.row}>{[5, 10, 15, 20].map((minutes) => <Chip key={minutes} title={`${minutes} min`} active={profile.minutes_per_day === minutes} onPress={() => setProfile({ ...profile, minutes_per_day: minutes })} />)}</View><Button title="Start my first lesson" onPress={() => void finishOnboarding()} /></ScrollView></SafeAreaView>;

  return <SafeAreaView style={styles.safe}><ScrollView contentContainerStyle={styles.page}>
    <View style={styles.top}><Text style={styles.logo}>mengo</Text><Text style={styles.streak}>🔥 {progress?.current_streak ?? 0} day streak</Text></View>
    {active ? <Conversation scenario={active} messages={messages} line={line} setLine={setLine} speak={speak} feedback={feedback} saveWord={saveWord} close={() => { setActive(null); setSessionId(null); }} /> : tab === "learn" ? <Learn scenarios={scenarios} progress={progress} begin={begin} /> : tab === "review" ? <Review /> : <Profile profile={profile} />}
  </ScrollView><View style={styles.nav}><Nav title="Learn" active={tab === "learn"} onPress={() => { setActive(null); setTab("learn"); }} /><Nav title="Review" active={tab === "review"} onPress={() => { setActive(null); setTab("review"); }} /><Nav title="Me" active={tab === "profile"} onPress={() => { setActive(null); setTab("profile"); }} /></View></SafeAreaView>;
}

function Learn({ scenarios, progress, begin }: { scenarios: Scenario[]; progress: Progress | null; begin: (scenario: Scenario) => void }) { return <><Text style={styles.h1}>Good to see you.</Text><Text style={styles.muted}>Small conversations, built for actual moments.</Text><View style={styles.hero}><Text style={styles.heroText}>{progress?.completed_lessons ?? 0} lessons complete</Text><Text style={styles.heroSub}>{progress?.total_minutes ?? 0} focused minutes · today counts</Text></View><Text style={styles.h2}>Practice a scenario</Text>{scenarios.map((s) => <Pressable key={s.id} onPress={() => void begin(s)} style={styles.card}><View><Text style={styles.cardTitle}>{s.title}</Text><Text style={styles.zh}>{s.title_zh}</Text><Text style={styles.muted}>{s.category} · {s.duration_minutes} min · {s.level}</Text></View><Text style={styles.arrow}>›</Text></Pressable>)}<View style={styles.paywall}><Text style={styles.h2}>Mengo Plus</Text><Text style={styles.muted}>Unlimited scenarios and deeper feedback. Demo pricing only—purchases are disabled locally.</Text><Text style={styles.price}>$9.99/month</Text><Button title="View plans" onPress={() => Alert.alert("Demo paywall", "Real Apple/Google billing is not enabled in this local MVP.")} /></View></> }
function Conversation({ scenario, messages, line, setLine, speak, feedback, saveWord, close }: { scenario: Scenario; messages: Message[]; line: string; setLine: (value: string) => void; speak: () => void; feedback: TutorFeedback; saveWord: (word: VocabularyWord) => void; close: () => void }) { return <><Pressable onPress={close}><Text style={styles.back}>‹ Back to scenarios</Text></Pressable><Text style={styles.h1}>{scenario.title}</Text><Text style={styles.muted}>{scenario.prompt}</Text><View style={styles.transcript}>{messages.map((message, index) => <View key={index} style={message.role === "You" ? styles.learnerBubble : styles.tutorBubble}><Text style={styles.messageRole}>{message.role}</Text><Text>{message.text}</Text>{message.secondary && <Text style={styles.pinyin}>{message.secondary}</Text>}</View>)}</View><TextInput value={line} onChangeText={setLine} placeholder="Type what you would say…" style={styles.input} /><Button title="● Send practice line (mock microphone)" onPress={() => void speak()} /><Text style={styles.caption}>This local MVP uses typed speech hints and deterministic mock speech services; it does not record audio.</Text><Text style={styles.h2}>Tutor feedback</Text><View style={styles.feedback}><Text>Pronunciation {Math.round(feedback.pronunciation_score * 100)}%</Text><Text>{feedback.grammar}</Text><Text>{feedback.vocabulary}</Text><Text>{feedback.tones}</Text></View><Text style={styles.h2}>Useful words</Text><View style={styles.row}>{scenario.vocabulary.map((word) => <Pressable key={word.hanzi} style={styles.word} onPress={() => void saveWord(word)}><Text style={styles.zh}>{word.hanzi}</Text><Text>{word.pinyin}</Text><Text style={styles.muted}>{word.english}</Text></Pressable>)}</View></> }
function Review() { const [items, setItems] = useState<Array<{ id: number; word: VocabularyWord }>>([]); useEffect(() => { void api.review().then(setItems).catch(() => setItems([])); }, []); return <><Text style={styles.h1}>Review queue</Text><Text style={styles.muted}>Save vocabulary from any scenario, then come back here.</Text>{items.length === 0 ? <View style={styles.empty}><Text>No words due. Save a word during a scenario.</Text></View> : items.map((item) => <View key={item.id} style={styles.card}><View><Text style={styles.zh}>{item.word.hanzi}</Text><Text>{item.word.pinyin} · {item.word.english}</Text></View><Pressable onPress={() => void api.gradeReview(item.id, 3).then(() => setItems((old) => old.filter((entry) => entry.id !== item.id)))}><Text style={styles.done}>Got it</Text></Pressable></View>)}</> }
function Profile({ profile }: { profile: LearnerProfile }) { return <><Text style={styles.h1}>Your plan</Text><View style={styles.card}><View><Text style={styles.cardTitle}>{profile.goal}</Text><Text style={styles.muted}>{profile.level} · {profile.minutes_per_day} minutes daily</Text></View></View><Text style={styles.h2}>Privacy promise</Text><Text style={styles.muted}>Mengo’s local mock experience does not send recordings or transcripts to analytics. Any future speech services require review and clear consent.</Text></> }
function Button({ title, onPress }: { title: string; onPress: () => void }) { return <Pressable style={styles.button} onPress={onPress}><Text style={styles.buttonText}>{title}</Text></Pressable> }
function Chip({ title, active, onPress }: { title: string; active: boolean; onPress: () => void }) { return <Pressable style={[styles.chip, active && styles.chipActive]} onPress={onPress}><Text style={active ? styles.chipTextActive : styles.chipText}>{title}</Text></Pressable> }
function Nav({ title, active, onPress }: { title: string; active: boolean; onPress: () => void }) { return <Pressable onPress={onPress}><Text style={active ? styles.navActive : styles.navText}>{title}</Text></Pressable> }
const styles = StyleSheet.create({ safe:{flex:1,backgroundColor:"#FFF8F0"},page:{padding:22,paddingBottom:88,gap:14},center:{flex:1,alignItems:"center",justifyContent:"center",gap:12,backgroundColor:"#FFF8F0"},top:{flexDirection:"row",justifyContent:"space-between",alignItems:"center"},logo:{fontSize:28,fontWeight:"800",color:"#D85B3F",letterSpacing:-1},streak:{backgroundColor:"#FFE2B8",padding:8,borderRadius:14},h1:{fontSize:29,fontWeight:"800",color:"#2C2825"},h2:{fontSize:19,fontWeight:"700",color:"#2C2825",marginTop:8},muted:{color:"#756D67",lineHeight:20},label:{fontWeight:"700",marginTop:8},input:{backgroundColor:"#FFF",borderWidth:1,borderColor:"#E9DDD1",borderRadius:14,padding:13,fontSize:16},row:{flexDirection:"row",flexWrap:"wrap",gap:8},chip:{borderWidth:1,borderColor:"#D8CAC0",paddingHorizontal:12,paddingVertical:9,borderRadius:20},chipActive:{backgroundColor:"#D85B3F",borderColor:"#D85B3F"},chipText:{color:"#554D48"},chipTextActive:{color:"#FFF",fontWeight:"700"},button:{backgroundColor:"#D85B3F",borderRadius:14,padding:15,alignItems:"center",marginTop:4},buttonText:{color:"white",fontWeight:"800"},hero:{backgroundColor:"#2A6659",padding:18,borderRadius:18,gap:5},heroText:{color:"#FFF",fontSize:20,fontWeight:"800"},heroSub:{color:"#D4F0E6"},card:{backgroundColor:"#FFF",borderRadius:16,padding:16,flexDirection:"row",justifyContent:"space-between",alignItems:"center",borderWidth:1,borderColor:"#F0E6DC"},cardTitle:{fontWeight:"800",fontSize:17,color:"#2C2825"},zh:{fontSize:18,fontWeight:"700",color:"#B34C35"},arrow:{fontSize:32,color:"#D85B3F"},paywall:{backgroundColor:"#FEE9C9",borderRadius:18,padding:18,gap:8,marginTop:6},price:{fontSize:22,fontWeight:"800",color:"#2C2825"},back:{color:"#D85B3F",fontWeight:"700"},transcript:{gap:10},learnerBubble:{alignSelf:"flex-end",maxWidth:"88%",backgroundColor:"#FCE0D7",padding:12,borderRadius:14},tutorBubble:{alignSelf:"flex-start",maxWidth:"88%",backgroundColor:"#FFF",padding:12,borderRadius:14},messageRole:{fontSize:12,fontWeight:"800",color:"#756D67",marginBottom:3},pinyin:{color:"#756D67",fontStyle:"italic",marginTop:4},caption:{fontSize:12,lineHeight:17,color:"#756D67"},feedback:{backgroundColor:"#E5F2ED",padding:15,borderRadius:14,gap:7},word:{backgroundColor:"#FFF",padding:12,borderRadius:12,minWidth:"44%"},empty:{padding:20,backgroundColor:"#FFF",borderRadius:16},done:{color:"#D85B3F",fontWeight:"800"},nav:{position:"absolute",bottom:0,left:0,right:0,backgroundColor:"#FFF",borderTopWidth:1,borderColor:"#EEE4DB",paddingHorizontal:42,paddingVertical:14,flexDirection:"row",justifyContent:"space-between"},navText:{color:"#756D67"},navActive:{color:"#D85B3F",fontWeight:"800"} });
