'use client'
import * as React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs) {
  return twMerge(clsx(inputs))
}

const DropdownMenu = ({ children }) => {
  const [open, setOpen] = React.useState(false)
  const containerRef = React.useRef(null)

  React.useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="relative inline-block text-left" ref={containerRef}>
      {React.Children.map(children, (child) => {
        if (child.type === DropdownMenuTrigger) {
          return React.cloneElement(child, { open, setOpen })
        }
        if (child.type === DropdownMenuContent) {
          return (
            <AnimatePresence>
              {open && React.cloneElement(child, { setOpen })}
            </AnimatePresence>
          )
        }
        return child
      })}
    </div>
  )
}

const DropdownMenuTrigger = ({ children, open, setOpen, className, ...props }) => {
  return (
    <button
      onClick={() => setOpen(!open)}
      className={cn("flex items-center outline-none", className)}
      {...props}
    >
      {children}
    </button>
  )
}

const DropdownMenuContent = ({ children, setOpen, className, align = "end", ...props }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: -10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: -10 }}
      transition={{ duration: 0.1 }}
      className={cn(
        "absolute z-50 mt-2 min-w-[8rem] overflow-hidden rounded-md border border-navy-600 bg-navy-800 p-1 text-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none",
        align === "end" ? "right-0" : "left-0",
        className
      )}
      {...props}
    >
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, { onClick: () => { 
            if (child.props.onClick) child.props.onClick()
            setOpen(false) 
          }})
        }
        return child
      })}
    </motion.div>
  )
}

const DropdownMenuItem = ({ children, className, onClick, ...props }) => {
  return (
    <div
      onClick={onClick}
      className={cn(
        "relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-navy-700 hover:text-teal-400 focus:bg-navy-700 focus:text-teal-400",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

const DropdownMenuLabel = ({ children, className, ...props }) => {
  return (
    <div className={cn("px-2 py-1.5 text-sm font-semibold", className)} {...props}>
      {children}
    </div>
  )
}

const DropdownMenuSeparator = ({ className, ...props }) => {
  return <div className={cn("-mx-1 my-1 h-px bg-navy-600", className)} {...props} />
}

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
}
