# I let an AI run my research loop. Here is where it took my research.

*Part 2 of Corporate Case Law. Code and every number: github.com/HadiFrt20/corporate-case-law*

---

## Where the research stood

Every company runs on rules nobody wrote down. The policy says "never more than 15% discount", but the deal desk quietly approves 30% for large customers facing a competitor. An AI agent that only reads the policy gets the company wrong.

In part 1 I tested an idea I call **Corporate Case Law**: dig those unwritten rules out of the company's own past decisions, and turn them into a short list of readable rules the agent must follow. A rule looks like this:

```
segment = 'Enterprise' AND competitor AND discount <= 30%  =>  APPROVE
```

Anyone can read it, test it, and switch it off. That is the whole appeal compared with a black-box model that makes the same decision without saying why.

The mechanism worked: on a simulated company with rules I had hidden on purpose, it found them. But as a method it lost. In the hardest test, a well-informed black-box model got about **3 more decisions right out of every 100**. The readable rules let harmful deals through, because a bad exception could slip in through another, legitimate rule.

So instead of iterating by hand, I let an AI run the research.

## How the loop works

I borrowed the structure of Andrej Karpathy's **autoresearch** project. It is a very small idea:

1. An AI agent may change exactly **one file**: the method that mines the rules.
2. A **scorer** it is not allowed to touch tests the result and returns one number.
3. If the number goes up, the change is kept. If it goes down, it is thrown away.
4. Repeat.

![The loop](img/b3_z01.png)
*Figure 1. The loop. I write the rules of the research (left), the agent edits one file (middle), a frozen scorer grades it (right), and the result is kept or thrown away.*

**The number** is simple: how often the readable rules make the right decision, minus how often the best of five black-box models does, in percentage points. Zero means a tie. Plus 0.1 means one more right decision per 1,000. Minus 3 means three fewer per 100, which is where part 1 ended.

**Who did what**, because it matters here:

- **An AI coding agent (Claude Code) wrote the code and ran about 40 experiments.** I did not write the method by hand.
- **A second AI model (GPT-6 Astra) reviewed the whole project four times**, looking for mistakes and for ways the agent might be fooling itself.
- **I set the goal and the rules of the game**, and read every review.

**Why the scorer is the important part.** An AI optimising a number will find any shortcut the scorer leaves open, without meaning to cheat. So the agent could only see the company's past, never the answer key. It could only hand back plain readable rules, at most 15, so no hidden model could sneak in. And it could only use one set of practice companies to decide what to keep. The real tests ran on companies generated at test time, that neither the agent nor I had ever seen.

## What the loop changed

The first round moved the score step by step, from clearly losing to slightly ahead on the practice companies.

![Round one, step by step](img/b3_z04.png)
*Figure 2. The score after each change the loop kept. Each bar is one kept change: from -1.14 points (part 1's method) to +0.18.*

Two of those changes are worth explaining, because they changed the idea itself, not just its settings.

### 1. It found the rule type part 1 was missing

Part 1's rules could only say "approve this exception". The loop found a way to say "**block this exception, because it hurts**". I call it an **overruling precedent**, after the legal term for a court striking down an earlier ruling.

Here is how it decides, with the numbers from the simulated company. Take one group of customers, say US mid-market. Compare two kinds of deals in that same group:

- deals approved **above** the 15% policy: **35%** of those customers renewed;
- deals approved **within** the policy: **85%** renewed.

Same customers, very different outcome. The exceptions are the problem, so the loop writes:

```
region = 'US' AND segment = 'Mid-market' AND discount > 15%  =>  REJECT
```

That is exactly the rogue approver I had hidden in the simulation.

![Overruling precedents](img/b3_z05.png)
*Figure 3. Comparing exceptions with normal deals of the SAME customers. The first version compared groups that were too broad, and blamed all US deals for one bad segment.*

The comparison has to be like with like. The first version looked at "all US deals", saw a drop, and blocked them all, even though the problem was only in one segment. The loop fixed that by checking that the drop holds in every sub-group before acting.

The effect was large. When the harm was strong, the readable rules caught **none** of the harmful deals without this rule type, and **all of them** with it.

### 2. It removed a step I thought was essential

Part 1 checked every new rule against a separate slice of recent decisions before accepting it, like a trial before a law is passed. The loop tried removing that check, and the score went up.

The reason is simple once you see it: setting aside four months of decisions for the trial left only eight months to find the rules, and rare rules did not have enough examples left to be found. The check still makes sense for rules from an untrusted source, such as rules an LLM proposes. For rules mined from the data, it was a cost.

## Then the real tests failed

The practice score looked good. The fresh test companies disagreed.

![The tests failed](img/b3_z07.png)
*Figure 4. Four tests on fresh companies. Each dot is the result, each line its uncertainty. All four fall short of the bar (dashed line).*

The bar was set before the tests: the readable rules may be **at most 0.25 points worse** than the best black box, about one extra mistake per 400 decisions. Four tests in a row failed it, and the last two were clearly worse, not just uncertain.

The cause was in the practice companies. I had written them by hand. The test companies were generated automatically, with rules like "deals **above 650k** get up to 28%". The rule miner only tried a few coarse thresholds, so the closest it could say was "**above 1,000k**". Deals between 650k and 1,000k that the hidden rule allowed were then wrongly rejected. The agent had been practising on the wrong kind of company.

## Round two: practise on the right companies

The second round fixed the practice set first: half of the practice companies were now generated the same way as the test ones. The loop immediately saw the problem it had missed, and three changes made the rules more precise.

![Round two](img/b3_z09.png)
*Figure 5. Round two: the score after each kept change, and one rule before and after (bottom).*

- **Finer thresholds.** Instead of round numbers, the miner tries every small step. The hidden "above 650k" rule is now found as "above 706k", close enough to stop the wrong rejections.
- **Precise beats broad.** When scoring a candidate rule, a wrong decision now costs twice as much as a right one earns. A broad rule that is right 90% of the time loses to a narrower one that is right 99% of the time.
- **Block only clear harm.** An overruling rule now fires only when the drop in renewals is clearly bigger than the threshold, not merely present. Small, noisy drops no longer trigger it.

Then one final test, written down in advance and run exactly once, on 24 new companies.

![The final test](img/b3_z10.png)
*Figure 6. All three final tests on one line. The last one passes the bar: the readable rules land on top of the best black box.*

**It passed.** About **6 readable rules** matched the best of five black-box models: **+0.03 points**, with a 95% range from -0.12 to +0.18. In plain terms: on new companies, the short list of readable rules made as many right decisions as the best model, within one or two decisions per thousand either way. Part 1 had ended three decisions per hundred behind.

## When does an AI research loop stop?

Karpathy's original never stops on its own. It runs until a human interrupts it. That is fine when you are training a model overnight. For research that makes claims, it is a trap: if you keep adjusting and re-testing, something eventually passes by luck.

![When it stops](img/b3_z11.png)
*Figure 7. Three stopping rules, from the smallest loop to the whole question.*

So the loop stops at three levels:

- **a round** ends after at most 12 experiments, or earlier if four in a row fail to help;
- **each round** gets exactly one final test, reported whatever it shows;
- **the question** "can readable rules match the black box?" is closed after three final tests. Two failed, one passed, and all three are public.

## What it does and does not mean

**What it shows.** On new simulated companies of the same kind, a few readable rules can match standard black-box models, while catching most harmful exceptions.

**What it does not show yet.** That it works on a real company. That it beats models tuned by an expert. And that six readable rules are actually easier for people to check and govern, which is the reason Corporate Case Law exists in the first place.

**What I take away from letting an AI run it.** The agent did not just find a better method. It forced a more honest way of testing one: a scorer it could not touch, tests written down before they ran, failures kept in the open, and a rule for when to stop. The method only started improving once that was in place.

The next step is not more simulation. It is one real dataset: the decisions, the written policy, and what happened to the customers afterwards.

---

**Code, tests and every number:** github.com/HadiFrt20/corporate-case-law (the `autoresearch/` folder). Karpathy's original: github.com/karpathy/autoresearch
