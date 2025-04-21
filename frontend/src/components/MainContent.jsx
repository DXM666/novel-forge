import React, { useState, useRef } from 'react';

// 主要内容区，纯文本编辑+AI与资料插入
const MainContent = ({ characters = [], locations = [], items = [], timeline = [], style = null, outline = null, onEditCharacter, onEditLocation, onEditItem }) => {
  const [aiText, setAiText] = useState('');
  const [loading, setLoading] = useState(false);
  const [continueLoading, setContinueLoading] = useState(false);
  const [continueError, setContinueError] = useState('');
  const [chapterContent, setChapterContent] = useState('');
  const [chapterLoading, setChapterLoading] = useState(false);
  const [history, setHistory] = useState([]); // 撤销栈
  const [redoStack, setRedoStack] = useState([]); // 重做栈
  const memoryId = 'test_memory';
  const textareaRef = useRef(null);
  // 插入角色/地点下拉菜单状态
  const [showCharacterList, setShowCharacterList] = useState(false);
  const [showLocationList, setShowLocationList] = useState(false);
  // 插入格式
  const [characterInsertFormat, setCharacterInsertFormat] = useState('@');
  const [locationInsertFormat, setLocationInsertFormat] = useState('#');
  const [itemInsertFormat, setItemInsertFormat] = useState('*');

  // 加载章节内容
  React.useEffect(() => {
    setChapterLoading(true);
    fetch(`http://localhost:8000/memory/${memoryId}`)
      .then(res => res.json())
      .then(data => {
        setChapterContent(typeof data.text === 'string' ? data.text : '');
      })
      .catch(() => setChapterContent(''))
      .finally(() => setChapterLoading(false));
  }, []);

  // 保存章节内容
  const handleSaveChapter = async () => {
    setChapterLoading(true);
    try {
      await fetch('http://localhost:8000/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ memory_id: memoryId, text: chapterContent })
      });
      alert('章节内容已保存！');
    } catch {
      alert('保存失败，请检查后端服务');
    }
    setChapterLoading(false);
  };

  // 记录历史
  const pushHistory = (content) => {
    setHistory(h => [...h, content]);
    setRedoStack([]);
  };

  // 撤销
  const handleUndo = () => {
    if (history.length === 0) return;
    setRedoStack(r => [chapterContent, ...r]);
    const last = history[history.length - 1];
    setHistory(history.slice(0, -1));
    setChapterContent(last);
  };

  // 重做
  const handleRedo = () => {
    if (redoStack.length === 0) return;
    setHistory(h => [...h, chapterContent]);
    const next = redoStack[0];
    setRedoStack(redoStack.slice(1));
    setChapterContent(next);
  };

  // 插入角色/地点/物品到光标处
  const handleInsertAtCursor = (text) => {
    setShowCharacterList(false);
    setShowLocationList(false);
    setShowItemList && setShowItemList(false);
    if (!textareaRef.current) return;
    const textarea = textareaRef.current;
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const before = chapterContent.slice(0, start);
    const after = chapterContent.slice(end);
    const newContent = before + text + after;
    setChapterContent(newContent);
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + text.length, start + text.length);
    }, 0);
  };
  // 插入物品下拉状态
  const [showItemList, setShowItemList] = useState(false);

  // 高亮渲染正文内容，支持点击弹窗详情
  const [highlightModal, setHighlightModal] = useState({ open: false, type: '', name: '', desc: '' });
  function highlightContent(text) {
    if (!text) return <span className="text-gray-400">（空）</span>;
    // 规则：@角色名、#地点名、*物品名
    // 角色
    let result = [];
    let lastIdx = 0;
    // 合并所有高亮规则
    const patterns = [
      { type: 'character', regex: /@([\u4e00-\u9fa5\w\-]+)/g, color: 'bg-indigo-100 text-indigo-700', list: characters },
      { type: 'location', regex: /#([\u4e00-\u9fa5\w\-]+)/g, color: 'bg-green-100 text-green-700', list: locations },
      { type: 'item', regex: /\*([\u4e00-\u9fa5\w\-]+)/g, color: 'bg-yellow-100 text-yellow-700', list: items },
    ];
    let idx = 0;
    let minNext = null;
    let minType = null;
    let minMatch = null;
    let minList = null;
    let minColor = '';
    while (true) {
      minNext = null;
      for (const pat of patterns) {
        pat.regex.lastIndex = lastIdx;
        const m = pat.regex.exec(text);
        if (m && (minNext === null || m.index < minNext)) {
          minNext = m.index;
          minType = pat.type;
          minMatch = m;
          minList = pat.list;
          minColor = pat.color;
        }
      }
      if (minNext === null) break;
      if (minNext > lastIdx) {
        result.push(text.slice(lastIdx, minNext));
      }
      const name = minMatch[1];
      const desc = (minList.find(x => x.name === name) || minList.find(x => x.title === name) || {}).desc || (minList.find(x => x.name === name) || minList.find(x => x.title === name) || {}).role || '';
      result.push(
        <span
          key={minType + '-' + name + '-' + minNext}
          className={`inline-block px-1 rounded cursor-pointer underline ${minColor}`}
          onClick={() => setHighlightModal({ open: true, type: minType, name, desc })}
          title={desc ? desc : name}
        >{minMatch[0]}</span>
      );
      lastIdx = minNext + minMatch[0].length;
    }
    if (lastIdx < text.length) {
      result.push(text.slice(lastIdx));
    }
    return result;
  }


  // AI优化语言
  const handleAIGeneratePolish = async () => {
    setLoading(true);
    setAiText('');
    try {
      const payload = {
        memory_id: memoryId,
        prompt: '请优化以下内容，使其语言更优美、更具风格：' + chapterContent,
        style: style?.name || '',
        characters: characters.map(c => c.name),
        locations: locations.map(l => l.name),
        timeline,
        outline: outline || {},
        content: chapterContent,
      };
      const res = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setAiText(data.text || 'AI未返回内容');
    } catch (e) {
      setAiText('请求失败，请检查后端服务');
    }
    setLoading(false);
  };

  // AI补全对话
  const handleAIGenerateDialogue = async () => {
    setLoading(true);
    setAiText('');
    try {
      const payload = {
        memory_id: memoryId,
        prompt: '请基于当前情节、角色和风格，为下文补全自然对话：' + chapterContent,
        style: style?.name || '',
        characters: characters.map(c => c.name),
        locations: locations.map(l => l.name),
        timeline,
        outline: outline || {},
        content: chapterContent,
      };
      const res = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setAiText(data.text || 'AI未返回内容');
    } catch (e) {
      setAiText('请求失败，请检查后端服务');
    }
    setLoading(false);
  };

  // AI风格转换
  const handleAIGenerateStyleTransfer = async () => {
    setLoading(true);
    setAiText('');
    try {
      const payload = {
        memory_id: memoryId,
        prompt: '请将以下内容转换为指定风格：' + chapterContent,
        style: style?.name || '',
        characters: characters.map(c => c.name),
        locations: locations.map(l => l.name),
        timeline,
        outline: outline || {},
        content: chapterContent,
      };
      const res = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setAiText(data.text || 'AI未返回内容');
    } catch (e) {
      setAiText('请求失败，请检查后端服务');
    }
    setLoading(false);
  };

  // AI续写
  const handleAIGenerateContinue = async () => {
    setLoading(true);
    setAiText('');
    try {
      const payload = {
        memory_id: memoryId,
        prompt: '请根据当前大纲、角色和风格，续写下文。',
        style: style?.name || '',
        characters: characters.map(c => c.name),
        locations: locations.map(l => l.name),
        timeline,
        outline: outline || {},
        content: chapterContent,
      };
      const res = await fetch('http://localhost:8000/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setAiText(data.text || 'AI未返回内容');
    } catch (e) {
      setAiText('请求失败，请检查后端服务');
    }
    setLoading(false);
  };

  // 智能续写
  const handleContinue = async () => {
    setContinueLoading(true);
    setContinueError('');
    try {
      const res = await fetch('http://localhost:8000/api/chapter/continue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: chapterContent })
      });
      const data = await res.json();
      if (data.continuation) {
        setChapterContent(chapterContent + data.continuation);
      } else {
        setContinueError('AI未返回续写内容');
      }
    } catch {
      setContinueError('AI续写失败，请检查后端服务');
    }
    setContinueLoading(false);
  };

  // ...

  return (
    <div className="flex-1 overflow-y-auto bg-white">
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* 标题输入 */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="Novel Title"
            className="w-full text-3xl font-bold border-none focus:outline-none focus:ring-0 placeholder-gray-300"
          />
          <input
            type="text"
            placeholder="Subtitle or tagline"
            className="w-full text-xl text-gray-500 border-none focus:outline-none focus:ring-0 placeholder-gray-300 mt-2"
          />
        </div>

        {/* 章节区域 */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Chapter 1: The Beginning</h2>
            <div className="flex space-x-2">
              <button className="p-1 text-gray-500 hover:text-gray-700">
                <i className="fas fa-cog"></i>
              </button>
              <button className="p-1 text-gray-500 hover:text-gray-700">
                <i className="fas fa-trash-alt"></i>
              </button>
            </div>
          </div>

          {/* 编辑内容 */}
          <div className="editor-content">
            <div className="flex flex-wrap gap-2 mb-2 items-center">
              <div className="relative group">
                <button className="px-2 py-1 bg-indigo-500 text-white rounded hover:bg-indigo-600 focus:ring-2 focus:ring-indigo-300 transition" type="button" onClick={() => setShowCharacterList(v => !v)} title="插入角色（@格式可被AI识别）">
                  插入角色
                </button>
                {showCharacterList && (
                  <div className="absolute z-10 mt-1 w-40 bg-white border rounded shadow-lg">
                    <div className="flex items-center px-3 py-1 text-xs text-gray-500">
                      格式：
                      <select className="ml-1 border rounded px-1 py-0.5 text-xs" value={characterInsertFormat} onChange={e => setCharacterInsertFormat(e.target.value)}>
                        <option value="@">@角色名</option>
                        <option value="">角色名</option>
                        <option value="[角色]">[角色]角色名</option>
                      </select>
                    </div>
                    {characters.length === 0 ? (
                      <div className="px-3 py-2 text-gray-400">无角色</div>
                    ) : (
                      characters.map((c, idx) => (
                        <div key={idx} className="px-3 py-2 hover:bg-indigo-100 cursor-pointer" onClick={() => handleInsertAtCursor(characterInsertFormat === '@' ? `@${c.name}` : characterInsertFormat === '[角色]' ? `[角色]${c.name}` : c.name)}>{c.name}</div>
                      ))
                    )}
                  </div>
                )}
              </div>
              <div className="relative group">
                <button className="px-2 py-1 bg-green-500 text-white rounded hover:bg-green-600 focus:ring-2 focus:ring-green-300 transition" type="button" onClick={() => setShowLocationList(v => !v)} title="插入地点（#格式可被AI识别）">
                  插入地点
                </button>
                {showLocationList && (
                  <div className="absolute z-10 mt-1 w-40 bg-white border rounded shadow-lg">
                    <div className="flex items-center px-3 py-1 text-xs text-gray-500">
                      格式：
                      <select className="ml-1 border rounded px-1 py-0.5 text-xs" value={locationInsertFormat} onChange={e => setLocationInsertFormat(e.target.value)}>
                        <option value="#">#地点名</option>
                        <option value="">地点名</option>
                        <option value="[地点]">[地点]地点名</option>
                      </select>
                    </div>
                    {locations.length === 0 ? (
                      <div className="px-3 py-2 text-gray-400">无地点</div>
                    ) : (
                      locations.map((l, idx) => (
                        <div key={idx} className="px-3 py-2 hover:bg-green-100 cursor-pointer" onClick={() => handleInsertAtCursor(locationInsertFormat === '#' ? `#${l.name}` : locationInsertFormat === '[地点]' ? `[地点]${l.name}` : l.name)}>{l.name}</div>
                      ))
                    )}
                  </div>
                )}
              </div>
              <div className="relative group">
                <button className="px-2 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600 focus:ring-2 focus:ring-yellow-300 transition" type="button" onClick={() => setShowItemList(v => !v)} title="插入物品（*格式可被AI识别）">
                  插入物品
                </button>
                {showItemList && (
                  <div className="absolute z-10 mt-1 w-40 bg-white border rounded shadow-lg">
                    <div className="flex items-center px-3 py-1 text-xs text-gray-500">
                      格式：
                      <select className="ml-1 border rounded px-1 py-0.5 text-xs" value={itemInsertFormat} onChange={e => setItemInsertFormat(e.target.value)}>
                        <option value="*">*物品名</option>
                        <option value="">物品名</option>
                        <option value="[物品]">[物品]物品名</option>
                      </select>
                    </div>
                    {items.length === 0 ? (
                      <div className="px-3 py-2 text-gray-400">无物品</div>
                    ) : (
                      items.map((it, idx) => (
                        <div key={idx} className="px-3 py-2 hover:bg-yellow-100 cursor-pointer" onClick={() => handleInsertAtCursor(itemInsertFormat === '*' ? `*${it.name}` : itemInsertFormat === '[物品]' ? `[物品]${it.name}` : it.name)}>{it.name}</div>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
            {/* 高亮渲染正文内容 */}
            <div className="w-full min-h-48 p-3 border border-gray-100 rounded mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-vertical whitespace-pre-wrap font-mono bg-gray-50/80 relative shadow-sm" style={{ minHeight: '12rem' }}>
              {highlightContent(chapterContent)}
              <textarea
                ref={textareaRef}
                className="absolute inset-0 w-full h-full opacity-0 cursor-text"
                value={chapterContent}
                onChange={(e) => setChapterContent(e.target.value)}
                readOnly={chapterLoading}
                placeholder="请在此输入章节内容..."
                spellCheck
                autoFocus
                onBlur={() => { setShowCharacterList(false); setShowLocationList(false); setShowItemList(false); }}
                style={{ resize: 'vertical' }}
              />
            </div>
            {/* 资料高亮点击弹窗 */}
            {highlightModal.open && (
              <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
                <div className="bg-white rounded-lg shadow-lg p-6 min-w-[320px]">
                  <h3 className="text-lg font-semibold mb-4">
                    {highlightModal.type === 'character' ? '角色' : highlightModal.type === 'location' ? '地点' : '物品'}详情
                  </h3>
                  <div className="mb-2 text-xl font-bold">{highlightModal.name}</div>
                  <textarea
                    className="w-full border rounded px-2 py-1 mb-4 text-gray-700 bg-gray-100 focus:bg-white focus:outline-none"
                    rows={3}
                    value={highlightModal.editDesc !== undefined ? highlightModal.editDesc : (highlightModal.desc || '')}
                    onChange={e => setHighlightModal(modal => ({ ...modal, editDesc: e.target.value }))}
                    placeholder="请输入简介/备注..."
                  />
                  <div className="flex justify-end space-x-2">
                    <button
                      className="px-4 py-2 rounded bg-gray-300 hover:bg-gray-400 text-gray-800"
                      onClick={() => setHighlightModal({ open: false })}
                    >关闭</button>
                    <button
                      className="px-4 py-2 rounded bg-green-600 hover:bg-green-700 text-white"
                      onClick={() => {
                        const { type, name, editDesc } = highlightModal;
                        if (!editDesc) return setHighlightModal(m => ({ ...m, editDesc: '' }));
                        if (type === 'character' && typeof onEditCharacter === 'function') {
                          const c = characters.find(x => x.name === name || x.title === name);
                          if (c) onEditCharacter({ ...c, desc: editDesc });
                        } else if (type === 'location' && typeof onEditLocation === 'function') {
                          const l = locations.find(x => x.name === name || x.title === name);
                          if (l) onEditLocation({ ...l, desc: editDesc });
                        } else if (type === 'item' && typeof onEditItem === 'function') {
                          const it = items.find(x => x.name === name || x.title === name);
                          if (it) onEditItem({ ...it, desc: editDesc });
                        }
                        setHighlightModal({ open: false });
                      }}
                    >保存</button>
                  </div>
                </div>
              </div>
            )}
            <div className="flex items-center space-x-2 mb-4">
              <button
                className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
                onClick={handleContinue}
                disabled={continueLoading || chapterLoading}
              >
                {continueLoading ? 'AI续写中...' : 'AI智能续写'}
              </button>
              {continueError && <span className="text-red-500 text-sm">{continueError}</span>}
            </div>
            <div className="flex items-center space-x-2 mb-4">
              <button
                className="px-4 py-2 bg-green-600 text-white rounded-md font-medium hover:bg-green-700 flex items-center disabled:opacity-60"
                onClick={handleSaveChapter}
                disabled={chapterLoading}
              >
                <i className="fas fa-save mr-2"></i> {chapterLoading ? '保存中...' : '保存章节'}
              </button>
              <button
                className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-60"
                onClick={handleUndo}
                disabled={history.length === 0}
              >撤销</button>
              <button
                className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-60"
                onClick={handleRedo}
                disabled={redoStack.length === 0}
              >重做</button>
            </div>
            {/* AI 建议示例 */}
            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
              <p className="text-sm text-blue-700">
                <span className="font-semibold">AI Suggestion:</span> Consider adding more sensory
                details about the rain to enhance atmosphere.
              </p>
            </div>
            {/* AI生成内容展示区 */}
            {aiText && (
              <div className="bg-gray-50 border-l-4 border-indigo-400 p-4 my-2 text-gray-900 whitespace-pre-line">
                <b>AI生成：</b>
                <div>{aiText}</div>
                <div className="flex space-x-2 mt-2">
                  <button className="px-2 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700" onClick={handleInsertAtCursor}>插入到光标处</button>
                  <button className="px-2 py-1 bg-green-600 text-white rounded hover:bg-green-700" onClick={handleAppendToEnd}>追加到末尾</button>
                  <button className="px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700" onClick={handleReplaceContent}>替换正文</button>
                </div>
              </div>
            )}
            <div className="flex items-center space-x-2 mt-4">
              <button
                className="px-4 py-2 bg-indigo-600 text-white rounded-md font-medium hover:bg-indigo-700 flex items-center disabled:opacity-60"
                onClick={handleAIGenerateContinue}
                disabled={loading}
              >
                <i className="fas fa-magic mr-2"></i> {loading ? '生成中...' : '智能续写'}
              </button>
              <button
                className="px-4 py-2 bg-amber-600 text-white rounded-md font-medium hover:bg-amber-700 flex items-center disabled:opacity-60"
                onClick={handleAIGeneratePolish}
                disabled={loading}
              >
                <i className="fas fa-feather-alt mr-2"></i> {loading ? '生成中...' : '优化语言'}
              </button>
              <button
                className="px-4 py-2 bg-green-600 text-white rounded-md font-medium hover:bg-green-700 flex items-center disabled:opacity-60"
                onClick={handleAIGenerateDialogue}
                disabled={loading}
              >
                <i className="fas fa-comments mr-2"></i> {loading ? '生成中...' : '补全对话'}
              </button>
              <button
                className="px-4 py-2 bg-purple-600 text-white rounded-md font-medium hover:bg-purple-700 flex items-center disabled:opacity-60"
                onClick={handleAIGenerateStyleTransfer}
                disabled={loading}
              >
                <i className="fas fa-paint-brush mr-2"></i> {loading ? '生成中...' : '风格迁移'}
              </button>
            </div>
            {/* 继续内容... */}
            {/* TODO: 更多段落和交互元素 */}
          </div>
        </div>

        {/* 新章节按钮 */}
        <div className="border-t border-gray-200 pt-6">
          <button className="px-4 py-2 bg-indigo-600 text-white rounded-md font-medium hover:bg-indigo-700 flex items-center">
            <i className="fas fa-plus mr-2"></i> Add New Chapter
          </button>
        </div>
      </div>
    </div>
  );
};

export default MainContent;
