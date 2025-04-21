import React, { useCallback, useMemo, useState, useImperativeHandle, forwardRef } from 'react';
import { createEditor, Transforms, Editor, Text, Element as SlateElement } from 'slate';
import { Slate, Editable, withReact, useSlate } from 'slate-react';
import { withHistory } from 'slate-history';

const initialValue = [
  { type: 'paragraph', children: [{ text: '' }] },
];

const LIST_TYPES = ['numbered-list', 'bulleted-list'];

const RichTextEditor = forwardRef(({ value, onChange, readOnly = false, editorRef }, ref) => {
  // 彻底兜底：Slate的value永远为合法节点数组
  const safeValue = Array.isArray(value) && value.length > 0 && value[0]?.type && value[0]?.children
    ? value
    : [{ type: 'paragraph', children: [{ text: '' }] }];
  // 调试：捕捉所有非法value传入
  if (process.env.NODE_ENV !== 'production') {
    if (!Array.isArray(value) || !value.length || !value[0]?.type || !value[0]?.children) {
      // eslint-disable-next-line
      console.error('[RichTextEditor] 非法value传入：', value, new Error().stack);
    }
  }
  const editor = useMemo(() => withHistory(withReact(createEditor())), []);

  useImperativeHandle(editorRef || ref, () => ({
    insertTextAtSelection: (text) => {
      if (!text) return;
      Transforms.insertText(editor, text);
    },
    setContent: (content) => {
      if (!content) return;
      Transforms.select(editor, Editor.start(editor, []));
      Transforms.delete(editor, { at: [] });
      editor.insertFragment(content);
    },
    getContent: () => editor.children,
  }), [editor]);

  // 工具栏按钮
  const renderToolbar = () => (
    <div className="flex mb-2 space-x-2">
      <MarkButton format="bold" icon={<i className="fas fa-bold" />} />
      <MarkButton format="italic" icon={<i className="fas fa-italic" />} />
      <BlockButton format="heading-one" icon={<i className="fas fa-heading" />} />
      <BlockButton format="bulleted-list" icon={<i className="fas fa-list-ul" />} />
      <BlockButton format="numbered-list" icon={<i className="fas fa-list-ol" />} />
      <BlockButton format="block-quote" icon={<i className="fas fa-quote-right" />} />
    </div>
  );

  // 渲染元素
  const renderElement = useCallback(props => {
    switch (props.element.type) {
      case 'heading-one':
        return <h1 className="text-2xl font-bold my-2" {...props.attributes}>{props.children}</h1>;
      case 'block-quote':
        return <blockquote className="border-l-4 border-indigo-400 pl-3 italic text-gray-600 my-2" {...props.attributes}>{props.children}</blockquote>;
      case 'bulleted-list':
        return <ul className="list-disc ml-6 my-1" {...props.attributes}>{props.children}</ul>;
      case 'numbered-list':
        return <ol className="list-decimal ml-6 my-1" {...props.attributes}>{props.children}</ol>;
      case 'list-item':
        return <li {...props.attributes}>{props.children}</li>;
      default:
        return <p {...props.attributes}>{props.children}</p>;
    }
  }, []);

  // 渲染文本样式
  const renderLeaf = useCallback(props => {
    let { children } = props;
    if (props.leaf.bold) {
      children = <strong>{children}</strong>;
    }
    if (props.leaf.italic) {
      children = <em>{children}</em>;
    }
    return <span {...props.attributes}>{children}</span>;
  }, []);

  // 全局兜底，彻底防止Slate报错
  return (
    <Slate editor={editor} value={safeValue} onChange={onChange}>
      {!readOnly && renderToolbar()}
      <Editable
        renderElement={renderElement}
        renderLeaf={renderLeaf}
        readOnly={readOnly}
        className="w-full min-h-48 p-3 border border-gray-200 rounded mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-vertical"
        placeholder="请在此输入章节内容..."
        spellCheck
        autoFocus
        onKeyDown={event => {
          if (!event.ctrlKey) return;
          switch (event.key) {
            case 'b':
              event.preventDefault();
              toggleMark(editor, 'bold');
              break;
            case 'i':
              event.preventDefault();
              toggleMark(editor, 'italic');
              break;
            default:
              break;
          }
        }}
      />
    </Slate>
  );
});

function toggleBlock(editor, format) {
  const isActive = isBlockActive(editor, format);
  const isList = LIST_TYPES.includes(format);
  Transforms.unwrapNodes(editor, {
    match: n => LIST_TYPES.includes(n.type),
    split: true,
  });
  const newType = isActive ? 'paragraph' : isList ? 'list-item' : format;
  Transforms.setNodes(editor, { type: newType });
  if (!isActive && isList) {
    const block = { type: format, children: [] };
    Transforms.wrapNodes(editor, block);
  }
}

function toggleMark(editor, format) {
  const isActive = isMarkActive(editor, format);
  if (isActive) {
    Editor.removeMark(editor, format);
  } else {
    Editor.addMark(editor, format, true);
  }
}

function isBlockActive(editor, format) {
  const [match] = Editor.nodes(editor, {
    match: n => n.type === format,
  });
  return !!match;
}

function isMarkActive(editor, format) {
  const marks = Editor.marks(editor);
  return marks ? marks[format] === true : false;
}

const BlockButton = ({ format, icon }) => {
  const editor = useSlate();
  return (
    <button
      className="px-2 py-1 bg-gray-100 rounded hover:bg-gray-300"
      onMouseDown={event => {
        event.preventDefault();
        toggleBlock(editor, format);
      }}
      title={format}
    >{icon}</button>
  );
};

const MarkButton = ({ format, icon }) => {
  const editor = useSlate();
  return (
    <button
      className="px-2 py-1 bg-gray-100 rounded hover:bg-gray-300"
      onMouseDown={event => {
        event.preventDefault();
        toggleMark(editor, format);
      }}
      title={format}
    >{icon}</button>
  );
};

// 已废弃
