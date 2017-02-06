The Elixir Cross Referencer
===========================

Elixir is a source code cross-referencer inspired by [LXR](https://en.wikipedia.org/wiki/LXR_Cross_Referencer). It's written in Python and its main purpose is to index every release of the Linux kernel while keeping a minimal footprint.

It uses Git as a source-code file store and Berkeley DB for cross-reference data. Internally, it indexes Git *blobs* instead of trees of files to avoid duplicating work and data. It has a straightforward data structure (reminiscent of older LXR releases) to keep queries simple and fast.
