const { chromium } = require('playwright');

const targetUrl = process.argv[2] || 'http://127.0.0.1:8134/ethan-white-lies-writing-speaking-context-lab.html';
const executablePath = process.env.CHROME_EXECUTABLE || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

(async () => {
  const browser = await chromium.launch({ headless: true, executablePath });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });

  try {
    await page.goto(targetUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(700);

    const requiredIds = ['evidenceLibrary', 'sourceBridge', 'answerModels', 'draftBuilder'];
    const idReport = await page.evaluate((ids) => ids.map((id) => ({
      id,
      count: document.querySelectorAll(`#${id}`).length,
      heading: document.getElementById(id)?.querySelector('h2')?.textContent || ''
    })), requiredIds);
    idReport.forEach((item) => assert(item.count === 1, `Expected exactly one #${item.id}, found ${item.count}`));

    await page.click('[data-jump-filter="writing"]');
    await page.waitForTimeout(400);
    const writingFilter = await page.evaluate(() => ({
      visible: [...document.querySelectorAll('.source-card')].filter((card) => getComputedStyle(card).display !== 'none').length,
      summary: document.getElementById('filterSummary').textContent,
      title: document.getElementById('currentSourceTitle').textContent
    }));
    assert(writingFilter.visible === 7, `Expected 7 writing sources, found ${writingFilter.visible}`);
    assert(/writing-move sources/.test(writingFilter.summary), 'Writing filter summary did not update');

    await page.click('[data-filter="all"]');
    await page.fill('#sourceSearch', 'gossip');
    await page.waitForTimeout(300);
    const gossipSearch = await page.evaluate(() => ({
      visible: [...document.querySelectorAll('.source-card')].filter((card) => getComputedStyle(card).display !== 'none').length,
      title: document.getElementById('currentSourceTitle').textContent
    }));
    assert(gossipSearch.visible >= 1, 'Source search for gossip returned no cards');
    assert(/gossip|Rumors/i.test(gossipSearch.title), `Unexpected search reader title: ${gossipSearch.title}`);

    await page.fill('#sourceSearch', 'zzzz-no-match');
    await page.waitForTimeout(200);
    const noMatch = await page.locator('#filterSummary').innerText();
    assert(/Try a broader search word/.test(noMatch), 'No-match source search does not show recovery guidance');
    await page.fill('#sourceSearch', '');

    await page.fill('#toneInput', 'Your answer is too vague.');
    await page.click('[data-tone="firm"]');
    const tone = await page.locator('#toneOutput').innerText();
    assert(/Firm feedback/.test(tone) && /too vague/.test(tone), 'Tone Transformer did not produce firm feedback');

    await page.click('#sourceBridge [data-add-draft]');
    const bridgeDraft = await page.locator('#draft').inputValue();
    assert(/white lie may solve/.test(bridgeDraft), 'Bridge Add to draft did not insert a sentence');
    await page.click('#copyDraft');
    await page.waitForTimeout(150);
    const copyStatus = await page.locator('#draftStatus').innerText();
    assert(/Copied/.test(copyStatus), `Copy draft did not report success: ${copyStatus}`);

    await page.fill('#draft', 'Although a white lie may seem kind, it can damage trust and credibility if it protects the speaker more than the listener. However, tactful honesty can preserve dignity while still giving useful feedback.');
    await page.waitForTimeout(150);
    const readiness = await page.evaluate(() => [...document.querySelectorAll('.ready-chip')].map((el) => ({
      text: el.textContent,
      ok: el.classList.contains('ok')
    })));
    assert(readiness.some((item) => /Contrast included/.test(item.text) && item.ok), 'Readiness meter did not detect contrast');
    assert(readiness.some((item) => /Core concept included/.test(item.text) && item.ok), 'Readiness meter did not detect core concept');

    await page.click('[data-timer-seconds="30"]');
    await page.waitForTimeout(1200);
    const timerRunning = await page.locator('#speakingTimer').innerText();
    assert(/^0:2[89]$/.test(timerRunning), `Timer did not start correctly: ${timerRunning}`);
    await page.click('#stopTimer');
    const timerStopped = await page.locator('#speakingTimer').innerText();
    assert(timerStopped === 'Ready', `Timer did not stop cleanly: ${timerStopped}`);

    await page.click('#focusReader');
    await page.waitForTimeout(150);
    const reader = await page.evaluate(() => ({
      focus: document.body.classList.contains('reader-focus'),
      button: document.getElementById('focusReader').textContent,
      overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth
    }));
    assert(reader.focus && /Balanced view/.test(reader.button), 'Reader focus mode did not activate');
    assert(!reader.overflow, 'Page has horizontal overflow');

    const mobilePage = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true });
    await mobilePage.goto(targetUrl, { waitUntil: 'domcontentloaded' });
    await mobilePage.waitForTimeout(700);
    const mobileInitial = await mobilePage.evaluate(() => ({
      overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      iframeHeight: Math.round(document.querySelector('iframe').getBoundingClientRect().height),
      navCount: document.querySelectorAll('.navlinks a,.navlinks button').length
    }));
    assert(!mobileInitial.overflow, 'Mobile page has horizontal overflow');
    assert(mobileInitial.iframeHeight >= 500, `Mobile source reader is too short: ${mobileInitial.iframeHeight}`);
    await mobilePage.click('[data-jump-filter="literature"]');
    await mobilePage.waitForTimeout(500);
    await mobilePage.fill('#sourceSearch', 'trust');
    await mobilePage.waitForTimeout(200);
    const mobileSearch = await mobilePage.evaluate(() => ({
      overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
      visible: [...document.querySelectorAll('.source-card')].filter((card) => getComputedStyle(card).display !== 'none').length,
      summary: document.getElementById('filterSummary').textContent
    }));
    assert(!mobileSearch.overflow, 'Mobile page overflows after source filtering');
    assert(mobileSearch.visible >= 1, 'Mobile source search found no trust sources');
    await mobilePage.close();

    console.log(JSON.stringify({
      ok: true,
      targetUrl,
      checks: {
        ids: idReport,
        writingFilter,
        gossipSearch,
        noMatch,
        tone: 'passed',
        bridgeDraft: 'passed',
        copyDraft: 'passed',
        readiness: 'passed',
        timer: 'passed',
        reader: 'passed',
        mobile: {
          initial: mobileInitial,
          search: mobileSearch
        }
      }
    }, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
