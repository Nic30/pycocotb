from contextlib import contextmanager
import distutils
from multiprocessing import Pool


@contextmanager
def monkey_patch_parallel_compilation(theread_pool: Pool):
    def parallelCCompile(self, sources, output_dir=None, macros=None, include_dirs=None,
                         debug=0, extra_preargs=None, extra_postargs=None, depends=None):
        # those lines are copied from distutils.ccompiler.CCompiler directly
        macros, objects, extra_postargs, pp_opts, build = self._setup_compile(
            output_dir, macros, include_dirs, sources, depends, extra_postargs)
        cc_args = self._get_cc_args(pp_opts, debug, extra_preargs)

        def _compile_obj(obj):
            try:
                src, ext = build[obj]
            except KeyError:
                return
            self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)

        # choose to compile using thread pool or sequentially
        if theread_pool is not None:
            _compile_map_fn = theread_pool.imap
        else:
            _compile_map_fn = map

        for _ in _compile_map_fn(_compile_obj, objects):
            pass

        return objects
    origina_compile = distutils.ccompiler.CCompiler.compile
    distutils.ccompiler.CCompiler.compile = parallelCCompile
    yield
    distutils.ccompiler.CCompiler.compile = origina_compile
