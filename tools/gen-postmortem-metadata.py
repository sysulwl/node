#!/usr/bin/env python

#
# gen-postmortem-metadata.py output_file.cc
#
# Creates debugging symbols to help navigate Node's internals using post-mortem
# debugging tools.
#

import os
import fnmatch
import re
from glob import glob
import sys


class DebugSymbol(object):
  type_ = 'int'
  _prefix = 'nodedbg_'

  def __init__(self, name, value, headers=[], type_=None):
    self.name = name
    self.value = value
    self.headers = headers
    self.type_ = type_ or DebugSymbol.type_

  @classmethod
  def get_headers(cls, debug_symbols):
    '''
    Return a list of headers without duplicates, preserving the order they were
    declared
    '''
    seen = set()
    headers = [debug_symbol.headers for debug_symbol in debug_symbols]
    headers = sum(headers, [])

    result = []
    for h in headers:
      if not h in seen:
        seen.add(h)
        result.append(h)

    return result

  @property
  def declare(self):
    return '{type} {prefix}{name};'.format(
      type=self.type_,
      prefix=self._prefix,
      name=self.name,
    )

  @property
  def fill(self):
    return '{prefix}{name} = {value};'.format(
      prefix=self._prefix,
      name=self.name,
      value=self.value,
    )


debug_symbols = [
  DebugSymbol(
    name='environment_context_idx_embedder_data',
    value='Environment::kContextEmbedderDataIndex',
    headers=['env.h'],
    type_='int',
  ),
  DebugSymbol(
    name='class__BaseObject__persistent_handle',
    value='offsetof(BaseObject, persistent_handle_)',
    headers=['base_object-inl.h'],
    type_='size_t',
  ),
  DebugSymbol(
    name='class__Environment__handleWrapQueue',
    value='offsetof(Environment, handle_wrap_queue_)',
    headers=['env.h'],
    type_='size_t',
  ),
  DebugSymbol(
    name='class__HandleWrap__node',
    value='offsetof(HandleWrap, handle_wrap_queue_)',
    headers=['handle_wrap.h'],
    type_='size_t',
  ),
  DebugSymbol(
    name='class__HandleWrapQueue__headOffset',
    value='offsetof(Environment::HandleWrapQueue, head_)',
    headers=['env.h'],
    type_='size_t',
  ),
  DebugSymbol(
    name='class__HandleWrapQueue__nextOffset',
    value='offsetof(ListNode<HandleWrap>, next_)',
    headers=['handle_wrap.h', 'util.h'],
    type_='size_t',
  ),
  DebugSymbol(
    name='class__Environment__reqWrapQueue',
    value='offsetof(Environment, req_wrap_queue_)',
    headers=['env.h'],
    type_='size_t',
  ),
  DebugSymbol(
    name='class__ReqWrap__node',
    value='offsetof(ReqWrap<uv_req_t>, req_wrap_queue_)',
    headers=['req_wrap.h'],
    type_='size_t',
  ),
  DebugSymbol(
    name='class__ReqWrapQueue__headOffset',
    value='offsetof(Environment::ReqWrapQueue, head_)',
    headers=['env.h'],
    type_='size_t',
  ),
  DebugSymbol(
    name='class__ReqWrapQueue__nextOffset',
    value='offsetof(ListNode<ReqWrap<uv_req_t>>, next_)',
    headers=['req_wrap.h', 'util.h'],
    type_='size_t',
  ),
]


template = '''
/*
 * This file is generated by {filename}.  Do not edit directly.
 */

// Need to import standard headers before redefining private, otherwise it
// won't compile
{standard_includes}

int GenDebugSymbol();

#define private friend int GenDebugSymbol(); private

{includes}

{declare_symbols}

namespace node {{

int GenDebugSymbol() {{
{fill_symbols}
return 1;
}}

int debug_symbols_generated = GenDebugSymbol();

}}
'''


def get_standard_includes():
  '''
  Try to find all standard C++ headers needed by node and its dependencies
  '''
  includes = set()
  regex = re.compile('#include *<([a-zA-Z0-9\-_]*)>')
  for src in ["src", "deps"]:
    for root, dirnames, filenames in os.walk(src):
      for filename in fnmatch.filter(filenames, '*.h'):
        f = open(os.path.join(root, filename), 'r')
        for line in f.readlines():
          match = regex.match(line)
          if match:
            includes.add(match.group(1))
  return sorted(includes)


def create_symbols_file():
  out = file(sys.argv[1], 'w')
  headers = DebugSymbol.get_headers(debug_symbols)
  includes = ['#include "{0}"'.format(header) for header in headers]
  includes = '\n'.join(includes)

  standard_includes = get_standard_includes()
  standard_includes = ['#include <{0}>'.format(include) for include in standard_includes]
  standard_includes = '\n'.join(standard_includes)

  declare_symbols = '\n'.join([symbol.declare for symbol in debug_symbols])
  fill_symbols = '\n'.join([symbol.fill for symbol in debug_symbols])

  out.write(template.format(
    filename=sys.argv[0],
    includes=includes,
    standard_includes=standard_includes,
    declare_symbols=declare_symbols,
    fill_symbols=fill_symbols,
  ))


if len(sys.argv) < 2:
  print('usage: {0} output.cc'.format(sys.argv[0]))
  sys.exit(2)


create_symbols_file()
