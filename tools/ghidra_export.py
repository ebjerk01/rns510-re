# Ghidra postScript: inventory + decompile functions near target strings
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
fm = currentProgram.getFunctionManager()
funcs = list(fm.getFunctions(True))
out = []
out.append("FUNCTION COUNT: %d" % fm.getFunctionCount())
# address range
mem = currentProgram.getMemory()
out.append("IMAGE: %s - %s" % (currentProgram.getMinAddress(), currentProgram.getMaxAddress()))
# find target strings and their containing functions
targets = ["bootMgrLax","speedLimitAdvice","dynamicDrivingSpeed","allow_context","SpeedLimit","TheftProtection","Testmode","hdTermFormat","MULTI_VERIFY"]
listing = currentProgram.getListing()
st = currentProgram.getSymbolTable()
found = {}
di = DecompInterface(); di.openProgram(currentProgram)
mon = ConsoleTaskMonitor()
# scan defined data for strings
data_it = listing.getDefinedData(True)
hits = []
count=0
for d in data_it:
    v = d.getValue()
    if v is None: continue
    s = str(v)
    for t in targets:
        if t in s:
            hits.append((d.getAddress(), s[:60], t))
            break
out.append("STRING HITS: %d" % len(hits))
done=set()
for addr, s, t in hits[:40]:
    refs = list(getReferencesTo(addr))
    out.append("STR %s %r <- %d refs" % (addr, s, len(refs)))
    for r in refs[:2]:
        fa = r.getFromAddress()
        fn = fm.getFunctionContaining(fa)
        if fn and fn.getEntryPoint() not in done and len(done)<6:
            done.add(fn.getEntryPoint())
            try:
                res = di.decompileFunction(fn, 60, mon)
                if res and res.decompileCompleted():
                    out.append("==== DECOMP %s (%s) size=%d ====" % (fn.getName(), fn.getEntryPoint(), fn.getBody().getNumAddresses()))
                    out.append(res.getDecompiledFunction().getC()[:4000])
            except Exception as e:
                out.append("decomp err %s" % e)
open("ghidra_export.txt","w").write("\n".join(out))
print("WROTE export, funcs=%d hits=%d" % (fm.getFunctionCount(), len(hits)))
