import React, { useState } from 'react';

/**
 * 小说大纲三层结构面板
 * 1. 故事骨架（核心冲突+5幕结构）
 * 2. 章节脉络（含关键情节点）
 * 3. 场景卡片（时间/地点/人物/冲突）
 *
 * 支持AI生成、动态调整、分支建议、伏笔提醒等
 */
const defaultOutline = {
  skeleton: '',
  chapters: [],
};



const OutlinePanel = ({ outline: propOutline = null, onOutlineChange, onGenerateOutline, onAdjustOutline }) => {
  const [outline, setOutline] = useState(propOutline || defaultOutline);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  // 章节弹窗状态
  const [chapterModal, setChapterModal] = useState({ open: false, type: '', idx: null });
  const [chapterForm, setChapterForm] = useState({ title: '', summary: '' });

  function openChapterModal(type, idx = null) {
    setChapterModal({ open: true, type, idx });
    if (type === 'edit' && typeof idx === 'number') {
      const c = outline.chapters[idx];
      setChapterForm({ title: c.title || '', summary: c.summary || '' });
    } else {
      setChapterForm({ title: '', summary: '' });
    }
  }
  function closeChapterModal() {
    setChapterModal({ open: false, type: '', idx: null });
    setChapterForm({ title: '', summary: '' });
  }
  function handleSaveChapterModal() {
    let newChapters = [...(outline.chapters || [])];
    if (chapterModal.type === 'add') {
      newChapters.push({ title: chapterForm.title, summary: chapterForm.summary, scenes: [] });
    } else if (chapterModal.type === 'edit' && typeof chapterModal.idx === 'number') {
      newChapters[chapterModal.idx] = { ...newChapters[chapterModal.idx], title: chapterForm.title, summary: chapterForm.summary };
    }
    setOutline({ ...outline, chapters: newChapters });
    if (onOutlineChange) onOutlineChange({ ...outline, chapters: newChapters });
    closeChapterModal();
  }
  function handleDeleteChapter(idx) {
    if (!window.confirm('确定要删除该章节吗？')) return;
    let newChapters = [...(outline.chapters || [])];
    newChapters.splice(idx, 1);
    setOutline({ ...outline, chapters: newChapters });
    if (onOutlineChange) onOutlineChange({ ...outline, chapters: newChapters });
  }


  // AI生成大纲
  const handleGenerate = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch('http://localhost:8000/api/outline/generate', { method: 'POST' });
      const data = await res.json();
      setOutline(data);
      if (onOutlineChange) onOutlineChange(data);
      if (onGenerateOutline) onGenerateOutline(data);
    } catch {
      setError('AI大纲生成失败，请检查后端服务');
    }
    setLoading(false);
  };

  // 动态调整大纲（如分支建议、伏笔提醒等）
  const handleAdjust = async (type, payload) => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch('http://localhost:8000/api/outline/adjust', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type, payload, outline }),
      });
      const data = await res.json();
      setOutline(data);
      if (onOutlineChange) onOutlineChange(data);
      if (onAdjustOutline) onAdjustOutline(data);
    } catch {
      setError('大纲调整失败，请检查后端服务');
    }
    setLoading(false);
  };

  // 监听props传入大纲变化
  React.useEffect(() => {
    if (propOutline) setOutline(propOutline);
  }, [propOutline]);

  return (
    <>
      <div className="bg-white rounded shadow p-4 h-full flex flex-col">
        <h2 className="text-xl font-bold">小说大纲</h2>
        <button className="px-3 py-1 rounded bg-indigo-600 text-white hover:bg-indigo-700" onClick={handleGenerate} disabled={loading}>
          {loading ? '生成中...' : 'AI生成大纲'}
        </button>
      </div>
      {error && <div className="text-red-500 mb-2">{error}</div>}
      {/* 故事骨架 */}
      <div className="mb-4">
        <h3 className="font-semibold text-indigo-700 mb-2">故事骨架</h3>
        <div className="bg-gray-50 rounded p-3 text-sm min-h-16 whitespace-pre-line">{outline.skeleton || '（AI生成后展示核心冲突与五幕结构）'}</div>
      </div>
      {/* 章节脉络 */}
      <div className="mb-4">
        <h3 className="font-semibold text-indigo-700 mb-2 flex items-center justify-between">
          章节脉络
          <button className="px-2 py-1 ml-2 text-xs rounded bg-green-500 text-white hover:bg-green-600" onClick={() => openChapterModal('add')}>新建章节</button>
        </h3>
        <div className="space-y-2">
          {outline.chapters && outline.chapters.length > 0 ? outline.chapters.map((chapter, idx) => (
            <div key={idx} className="bg-indigo-50 rounded p-2 flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <div className="font-semibold">第{idx + 1}章</div>
                <div className="space-x-1">
                  <button className="px-2 py-0.5 text-xs rounded bg-yellow-500 text-white hover:bg-yellow-600" onClick={() => openChapterModal('edit', idx)}>编辑</button>
                  <button className="px-2 py-0.5 text-xs rounded bg-red-500 text-white hover:bg-red-600" onClick={() => handleDeleteChapter(idx)}>删除</button>
                </div>
              </div>
              <div className="text-gray-700 whitespace-pre-line">{chapter.summary || '（AI生成后展示章节概要）'}</div>
              {/* 场景卡片 */}
              {chapter.scenes && chapter.scenes.length > 0 && (
                <div className="ml-4 mt-2 space-y-1">
                  {chapter.scenes.map((scene, sidx) => (
                    <div key={sidx} className="bg-white border border-gray-200 rounded px-2 py-1">
                      <div className="font-medium mb-1">场景{sidx + 1}：{scene.title || '（场景标题）'}</div>
                      <div className="text-gray-700 whitespace-pre-line">{scene.summary || '（AI生成后展示场景内容）'}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )) : <div className="text-gray-400">（AI生成后展示章节脉络）</div>}
        </div>
        {/* 章节编辑弹窗 */}
        {chapterModal.open && (
          <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-30 z-50">
            <div className="bg-white rounded shadow-lg p-6 w-80">
              <h4 className="font-bold mb-2">{chapterModal.type === 'add' ? '新建章节' : '编辑章节'}</h4>
              <input
                className="w-full border rounded px-2 py-1 mb-2"
                placeholder="章节标题"
                value={chapterForm.title}
                onChange={e => setChapterForm(f => ({ ...f, title: e.target.value }))}
              />
              <textarea
                className="w-full border rounded px-2 py-1 mb-2"
                placeholder="章节概要"
                value={chapterForm.summary}
                onChange={e => setChapterForm(f => ({ ...f, summary: e.target.value }))}
                rows={3}
              />
              <div className="flex justify-end gap-2">
                <button className="px-3 py-1 rounded bg-gray-300 hover:bg-gray-400" onClick={closeChapterModal}>取消</button>
                <button className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700" onClick={handleSaveChapterModal}>保存</button>
              </div>
            </div>
          </div>
        )}
      </div>
      {/* 动态大纲调整建议 */}
      <div className="mt-auto">
        <button className="mr-2 px-3 py-1 rounded bg-purple-600 text-white hover:bg-purple-700" onClick={() => handleAdjust('suggest_branch', {})} disabled={loading}>情节分支建议</button>
        <button className="mr-2 px-3 py-1 rounded bg-green-600 text-white hover:bg-green-700" onClick={() => handleAdjust('remind_foreshadow', {})} disabled={loading}>伏笔回收提醒</button>
        <button className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700" onClick={() => handleAdjust('analyze_pacing', {})} disabled={loading}>节奏分析</button>
      </div>
    </>
  );
};

export default OutlinePanel;

