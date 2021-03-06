from os import path
import os
import unittest

from hdlConvertor import HdlConvertor
from hdlConvertorAst.hdlAst._structural import HdlModuleDec, HdlModuleDef
from hdlConvertorAst.language import Language
from hdlConvertorAst.to.verilog.verilog2005 import ToVerilog2005
from hdlConvertorAst.to.vhdl.vhdl2008 import ToVhdl2008


try:
    # python2
    from StringIO import StringIO
    from io import open
except ImportError:
    # python3
    from io import StringIO


TEST_DIR = os.path.abspath(os.path.dirname(__file__))

VHDL = Language.VHDL
VERILOG = Language.VERILOG
SV = Language.SYSTEM_VERILOG

LANG_SUFFIX = {
    VHDL: ".vhd",
    VERILOG: ".v",
    SV: ".sv",
    Language.HDLCONVERTOR_JSON: ".json"
}


def get_language_path(lang_dir, language):
    if lang_dir is None:
        if language.is_system_verilog():
            lang_dir = os.path.join("sv_test", "others")
        elif language.is_verilog():
            lang_dir = "verilog"
        elif language.is_vhdl():
            lang_dir = "vhdl"
        elif language == Language.HDLCONVERTOR_JSON:
            lang_dir = "json"
        else:
            raise ValueError(language)
    return lang_dir


def get_to_hdl_cls(language):
    if language == VERILOG or language == SV:
        return ToVerilog2005
    elif language == VHDL:
        return ToVhdl2008
    else:
        raise NotImplementedError(language)


def parseFile(fname, language, lang_dir=None):
    lang_dir = get_language_path(lang_dir, language)
    inc_dir = path.join(TEST_DIR, lang_dir)
    f = path.join(TEST_DIR, lang_dir, fname)
    c = HdlConvertor()
    res = c.parse([f, ], language, [inc_dir], debug=True)
    return f, res


def _default_to_hdl(context, language, buff):
    to_hdl_cls = get_to_hdl_cls(language)
    ser = to_hdl_cls(buff)
    ser.visit_HdlContext(context)


class HdlParseTC(unittest.TestCase):
    """
    A base class for HDL parser tests
    """
    def translateWithRef(self, fname, src_lang, dst_lang, ref_fname=None,
                         src_lang_dir=None,
                         dst_lang_dir=None, to_hdl=_default_to_hdl):
        if ref_fname is None:
            ref_fname, _ = os.path.splitext(fname)
            ref_fname += LANG_SUFFIX[dst_lang]

        src_lang_dir = get_language_path(src_lang_dir, src_lang)
        _, res = parseFile(fname, src_lang, lang_dir=src_lang_dir)

        buff = StringIO()
        # import sys
        # buff = sys.stdout
        # serialize a HDL code to a buff
        to_hdl(res, dst_lang, buff)

        dst_lang_dir = get_language_path(dst_lang_dir, dst_lang)
        ref_file = path.join(TEST_DIR, dst_lang_dir,
                             "expected", ref_fname)
        res_str = buff.getvalue()
        # if fname == "aes.v":
        #     with open(ref_file, "w") as f:
        #         f.write(res_str)

        with open(ref_file, encoding="utf-8") as f:
            ref = f.read()

        self.assertEqual(ref, res_str)

    def parseWithRef(self, fname, language, lang_dir=None,
                     ref_fname=None, to_hdl=_default_to_hdl):
        """
        Parse file and compare it with a reference file.

        :param fname: name of a file to parse
        :type fname: str
        :type language: Language
        :param ref_fname: name of reference file in the case it is not the same
            (relative to "expected/" )
        :param lang_dir: path relative to a test directory where test file is stored
        :param transform: a function which can be used to modify a HdlContext
            pefore transformation to a target language
        """

        if ref_fname is None:
            ref_fname = fname

        lang_dir = get_language_path(lang_dir, language)
        _, res = parseFile(fname, language, lang_dir=lang_dir)

        buff = StringIO()
        # import sys
        # buff = sys.stdout

        # serialize a HDL code to a buff
        to_hdl(res, language, buff)

        ref_file = path.join(TEST_DIR, lang_dir,
                             "expected", ref_fname)
        res_str = buff.getvalue()
        # if fname == "aes.v":
        #     with open(ref_file, "w") as f:
        #         f.write(res_str)

        with open(ref_file, encoding="utf-8") as f:
            ref = f.read()

        self.assertEqual(ref, res_str)

    def check_obj_names(self, context, obj_cls, names):
        if obj_cls == HdlModuleDec:
            filtered = []
            for o in context.objs:
                if isinstance(o, HdlModuleDef) and o.dec is not None:
                    filtered.append(o.dec.name)
        else:
            filtered = [o.name for o in context.objs if isinstance(o, obj_cls)]
        self.assertSequenceEqual(names, filtered)

    def find_obj_by_name(self, context, obj_cls, name):
        if obj_cls == HdlModuleDec:
            for o in context.objs:
                if (isinstance(o, HdlModuleDec) and o.name == name) or\
                        (isinstance(o, HdlModuleDef) and o.dec.name == name):
                    return o.dec

        for o in context.objs:
            if isinstance(o, obj_cls) and o.name == name:
                return o
