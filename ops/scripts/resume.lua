-- pandoc filter for the resume export: wrap the body in <div class="resume">
-- mark bold-only paragraphs as .label, and mark the contact line (first paragraph mentioning Email/Mobile/Phone) as .contact
local done = false
function Para(el)
  -- a paragraph that is only bold text is a sub-heading label ("1) Delivery")
  if #el.content == 1 and el.content[1].t == "Strong" then
    return pandoc.Div({el}, pandoc.Attr("", {"label"}))
  end
  if done then return nil end
  local t = pandoc.utils.stringify(el)
  if t:match("Email") or t:match("Mobile") or t:match("Phone") then
    done = true
    return pandoc.Div({el}, pandoc.Attr("", {"contact"}))
  end
end
function Emph(el) return el.content end   -- no italics, ever
function Pandoc(doc)
  doc.blocks = {pandoc.Div(doc.blocks, pandoc.Attr("", {"resume"}))}
  return doc
end
